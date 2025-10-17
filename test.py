import os
import sys
import time
import traceback

import torch
import torchaudio

from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import Xtts


def assert_file_exists(path: str, description: str) -> None:
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Missing {description}: {path}")


def get_repo_root() -> str:
    return os.path.abspath(os.path.dirname(__file__))


def split_text_into_chunks(text: str, max_chars: int = 300) -> list[str]:
    """Split text into chunks that are safe for XTTS processing."""
    # Split by sentences first (periods, exclamation marks, question marks)
    sentences = []
    current_sentence = ""
    
    for char in text:
        current_sentence += char
        if char in ['،', '.', '!', '?', '؛', '\n']:
            sentences.append(current_sentence.strip())
            current_sentence = ""
    
    if current_sentence.strip():
        sentences.append(current_sentence.strip())
    
    # Group sentences into chunks
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        if len(current_chunk + sentence) <= max_chars:
            current_chunk += sentence + " "
        else:
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
            current_chunk = sentence + " "
    
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    
    return chunks


def main() -> None:
    start_time = time.time()

    if not torch.cuda.is_available():
        raise RuntimeError(
            "CUDA is not available. Please run inside WSL with a CUDA-enabled PyTorch build and GPU drivers."
        )

    device = torch.device("cuda")

    repo_root = get_repo_root()
    model_dir = os.path.join(repo_root, "OmarSamir", "EGTTS-V0.1")

    config_path = os.path.join(model_dir, "config.json")
    vocab_path = os.path.join(model_dir, "vocab.json")
    checkpoint_dir = model_dir  # contains model.pth
    speaker_wav = os.path.join(repo_root, "speaker.mp3")

    assert_file_exists(config_path, "config.json")
    assert_file_exists(vocab_path, "vocab.json")
    assert_file_exists(os.path.join(checkpoint_dir, "model.pth"), "model.pth")
    assert_file_exists(speaker_wav, "speaker reference wav")

    text = os.environ.get("EGTTS_TEXT", """بُص يا سيدي، إحنا كعربيات ماشية في شوارع القاهرة طول النهار والليل، الدنيا دي ليها طابع خاص. تلاقي الصبح وانت رايح شغلك زحمة من أول ما تنزل من بيتك، الكلاكسات شغّالة، وواحد معدّي من قدامك عادي خالص كإن الشارع بتاعه، وواحدة ست قاعدة على الرصيف بتبيع عيش أو خضار وصوتها مالي المكان. وفي وسط الدوشة دي تلاقي الناس برضه بتضحك وتهزر، واحد بيقول للتاني: "إيه يا عم مش تسيبلي سنتي أمشي فيه؟" والتاني يرد عليه ضاحك: "طب ما توسّع إنت الأول."

بالليل، الصورة بتتغيّر شوية. تلاقي القهاوي مليانة ناس، شباب قاعدين على الطربيزة قدامهم كوبايات شاي سخن وأرجيلة مولّعة، وكل واحد عايش في موضوع مختلف. في واحد بيتكلم عن الكورة، والتاني بيشتكي من الشغل، والتالت بيخطط مع أصحابه يسافروا إسكندرية آخر الأسبوع "يفضّوا دماغهم". الجو بيبقى أخف من الصبح، رغم إن الشوارع برضه مش فاضية.

والأجمل في الموضوع إن مهما كانت الضغوط والزحمة والظروف، المصريين عندهم قدرة غريبة يخلّوا أي موقف يتقلب هزار وضحك. يعني ممكن تبقى واقف في طابور طويل ومستني دورك، وفجأة تلاقي الناس اللي واقفة جنبك بتتكلم وتضحك مع بعض كإنهم يعرفوا بعض من زمان.

باختصار كده، الحياة في مصر شبه فيلم طويل، فيه جد وفيه هزار، فيه تعب بس فيه روح حلوة بتخلي الواحد يكمل.""")
    temperature = float(os.environ.get("EGTTS_TEMPERATURE", "0.6"))
    language = os.environ.get("EGTTS_LANGUAGE", "ar")
    
    # Split text into manageable chunks
    text_chunks = split_text_into_chunks(text)
    print(f"Split text into {len(text_chunks)} chunks")

    print("Loading EGTTS (XTTS v2) model...")
    config = XttsConfig()
    config.load_json(config_path)
    model = Xtts.init_from_config(config)

    use_deepspeed = False
    try:
        import deepspeed  # noqa: F401

        use_deepspeed = True
    except Exception:
        print("deepspeed not found; continuing without it.")

    model.load_checkpoint(
        config,
        checkpoint_dir=checkpoint_dir,
        use_deepspeed=use_deepspeed,
        vocab_path=vocab_path,
    )

    model.to(device)
    model.eval()

    print("Computing speaker conditioning latents...")
    with torch.inference_mode():
        gpt_cond_latent, speaker_embedding = model.get_conditioning_latents(audio_path=[speaker_wav])

    # Process each chunk
    all_audio_files = []
    base_name = "arabic_tts"
    
    for i, chunk in enumerate(text_chunks):
        print(f"Processing chunk {i+1}/{len(text_chunks)}: {chunk[:50]}...")
        
        with torch.inference_mode():
            out = model.inference(
                chunk,
                language,
                gpt_cond_latent,
                speaker_embedding,
                temperature=temperature,
            )

        wav = torch.tensor(out["wav"]).unsqueeze(0)
        sample_rate = 24000

        # Generate unique filename for this chunk
        chunk_filename = f"{base_name}_part_{i+1:02d}.wav"
        out_path = os.path.join(repo_root, chunk_filename)
        
        # If file exists, add counter
        counter = 1
        original_path = out_path
        while os.path.exists(out_path):
            name, ext = os.path.splitext(original_path)
            out_path = f"{name}_{counter}{ext}"
            counter += 1
        
        torchaudio.save(out_path, wav.cpu(), sample_rate)
        all_audio_files.append(out_path)
        print(f"Saved chunk {i+1} to: {out_path}")

    # Concatenate all audio files into one final file
    print("\nConcatenating all audio chunks...")
    concatenated_wav = None
    
    for file_path in all_audio_files:
        wav_data, sample_rate = torchaudio.load(file_path)
        if concatenated_wav is None:
            concatenated_wav = wav_data
        else:
            concatenated_wav = torch.cat([concatenated_wav, wav_data], dim=1)
    
    # Save the final concatenated file
    final_filename = f"{base_name}_complete.wav"
    final_path = os.path.join(repo_root, final_filename)
    
    # If file exists, add counter
    counter = 1
    original_final_path = final_path
    while os.path.exists(final_path):
        name, ext = os.path.splitext(original_final_path)
        final_path = f"{name}_{counter}{ext}"
        counter += 1
    
    torchaudio.save(final_path, concatenated_wav, sample_rate)
    
    elapsed = time.time() - start_time
    print(f"\nGenerated {len(all_audio_files)} individual audio files:")
    for file_path in all_audio_files:
        print(f"  - {os.path.basename(file_path)}")
    print(f"\nFinal concatenated file: {os.path.basename(final_path)}")
    print(f"Done in {elapsed:.2f}s on device: {device}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("Error during TTS execution:", str(e))
        traceback.print_exc()
        sys.exit(1)

