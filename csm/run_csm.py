import os
import torch
import torchaudio
from huggingface_hub import hf_hub_download
from generator import load_csm_1b, Segment
from dataclasses import dataclass

# Disable Triton compilation
os.environ["NO_TORCH_COMPILE"] = "1"

# Default prompts are available at https://hf.co/sesame/csm-1b
prompt_filepath_conversational_a = hf_hub_download(
    repo_id="sesame/csm-1b",
    filename="prompts/conversational_a.wav"
)
prompt_filepath_conversational_b = hf_hub_download(
    repo_id="sesame/csm-1b",
    filename="prompts/conversational_b.wav"
)

SPEAKER_PROMPTS = {
    "conversational_a": {
        "text": (
            "I'm a Chinese woman, my English has a heavy Chinese accent"
        ),
        "audio": prompt_filepath_conversational_a
    },
    "conversational_b": {
        "text": (
            "我是个中国女人，我说英文的时候中国口音很重"
        ),
        "audio": prompt_filepath_conversational_b
    }
}

def load_prompt_audio(audio_path: str, target_sample_rate: int) -> torch.Tensor:
    audio_tensor, sample_rate = torchaudio.load(audio_path)
    audio_tensor = audio_tensor.squeeze(0)
    # Resample is lazy so we can always call it
    audio_tensor = torchaudio.functional.resample(
        audio_tensor, orig_freq=sample_rate, new_freq=target_sample_rate
    )
    return audio_tensor

def prepare_prompt(text: str, speaker: int, audio_path: str, sample_rate: int) -> Segment:
    audio_tensor = load_prompt_audio(audio_path, sample_rate)
    return Segment(text=text, speaker=speaker, audio=audio_tensor)

def main():
    # Select the best available device, skipping MPS due to float64 limitations
    if torch.cuda.is_available():
        device = "cuda"
    else:
        device = "cpu"
    print(f"Using device: {device}")

    # Load model
    generator = load_csm_1b(device, use_local_tokenizer=True, local_tokenizer_path="../Llama-3.2-1B")

    # Prepare prompts
    prompt_a = prepare_prompt(
        SPEAKER_PROMPTS["conversational_a"]["text"],
        0,
        SPEAKER_PROMPTS["conversational_a"]["audio"],
        generator.sample_rate
    )

    prompt_b = prepare_prompt(
        SPEAKER_PROMPTS["conversational_b"]["text"],
        1,
        SPEAKER_PROMPTS["conversational_b"]["audio"],
        generator.sample_rate
    )

    # Generate conversation
    conversation = [
        {"text": "Your bluetooth device is ready to pair", "speaker_id": 0}
    ]

    # Generate each utterance
    generated_segments = []
    prompt_segments = [prompt_a, prompt_b]

    for utterance in conversation:
        print(f"Generating: {utterance['text']}")
        audio_tensor = generator.generate(
            text=utterance['text'],
            speaker=utterance['speaker_id'],
            context=prompt_segments + generated_segments,
            max_audio_length_ms=10_000,
        )
        generated_segments.append(Segment(text=utterance['text'], speaker=utterance['speaker_id'], audio=audio_tensor))

    # Concatenate all generations
    all_audio = torch.cat([seg.audio for seg in generated_segments], dim=0)
    torchaudio.save(
        "full_conversation.wav",
        all_audio.unsqueeze(0).cpu(),
        generator.sample_rate
    )
    print("Successfully generated full_conversation.wav")

if __name__ == "__main__":
    main() 