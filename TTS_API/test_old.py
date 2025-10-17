import os
from google.cloud import texttospeech

# في حالة ما كنتش عرّفت المتغير في التيرمنال
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "tts-key.json"

# إنشاء عميل Text-to-Speech
client = texttospeech.TextToSpeechClient()

voices = client.list_voices()


def _get_voice_by_name(all_voices, voice_name: str):
    return next((v for v in all_voices if v.name == voice_name), None)


text = """في حارة صغيرة في قلب القاهرة القديمة، كان فيه واحد اسمه عوضين، راجل بسيط شغال سمكري، بس عنده سر محدش يعرفه. بالليل بعد ما المحل بيقفل، بيطلع فوق السطح يفتح صندوق نحاس قديم ورثه عن جده، جواه مصباح غريب كل ما يلمعه يطلع منه عفريت، بس مش أي عفريت... ده عفريت مصري، بيحب الكشري والمزيكا الشعبي 😅.
في يوم العفريت قاله: "اختار أمنية واحدة يا عوضين، وأنا أحققها!"
عوضين فكر وقاله: "عايز محل كبير في وسط البلد، ولا عمر الزباين يقلّ!"
العفريت ضحك وقاله: "خلاص يا بيه، بس استنى لما أخلص طاجن الملوخية الأول!"
ومن ساعتها، محل عوضين بقى أشهر سمكري في مصر... بس كل ما حد يسأله عن سر نجاحه، يضحك ويقول: "كلها بركة العفريت اللي بيحب الملوخية!"""
synthesis_input = texttospeech.SynthesisInput(text=text)

audio_config = texttospeech.AudioConfig(
    audio_encoding=texttospeech.AudioEncoding.MP3
)

def _sanitize_filename(name: str) -> str:
    return "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in name)

# الأصوات العربية اللي انت مرتاح لها (الأول ذكر - التاني أنثى)
preferred_voice_names = [
    "ar-XA-Chirp3-HD-Algenib",
    "ar-XA-Chirp3-HD-Despina",
]

# اختيار النوع: male الافتراضي أو female عبر متغير VOICE_GENDER
gender_choice = os.getenv("VOICE_GENDER", "male").lower()
idx = 1 if gender_choice == "female" else 0

# تأمين وجود الصوت المطلوب
if idx >= len(preferred_voice_names):
    idx = 0

selected_names = [preferred_voice_names[idx]]

print(f"\n🎧 Generating sample for: {selected_names[0]} (gender={gender_choice})...")
for name in selected_names:
    v = _get_voice_by_name(voices.voices, name)
    if not v:
        print(f"✖ Voice not found in account: {name}")
        continue
    try:
        lang_code = v.language_codes[0] if v.language_codes else "ar-XA"
        voice_params = texttospeech.VoiceSelectionParams(
            language_code=lang_code,
            name=v.name,
            ssml_gender=v.ssml_gender,
        )
        resp = client.synthesize_speech(
            input=synthesis_input,
            voice=voice_params,
            audio_config=audio_config,
        )
        fname = f"{_sanitize_filename(v.name)}.mp3"
        with open(fname, "wb") as f:
            f.write(resp.audio_content)
        print(f"✔ Saved {fname}")
    except Exception as e:
        print(f"✖ Failed for {name}: {e}")
