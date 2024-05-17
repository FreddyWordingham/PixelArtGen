import argparse
import os

from diffusers import DiffusionPipeline, LCMScheduler
import torch


OUTPUT_DIRECTORY = "output"


def read_input():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", type=str, help="Prompt to generate images")
    parser.add_argument(
        "--num_images", type=int, help="Number of images to generate", default=1
    )
    parser.add_argument(
        "--resolution", type=int, help="Resolution of the images", default=None
    )
    args = parser.parse_args()
    return args.prompt, args.num_images, args.resolution


def init_pipe():
    model_id = "stabilityai/stable-diffusion-xl-base-1.0"
    lcm_lora_id = "latent-consistency/lcm-lora-sdxl"
    pipe = DiffusionPipeline.from_pretrained(model_id, variant="fp16")
    pipe.scheduler = LCMScheduler.from_config(pipe.scheduler.config)
    pipe.load_lora_weights(lcm_lora_id, adapter_name="lora")
    pipe.load_lora_weights("./pixel-art-xl.safetensors", adapter_name="pixel")
    pipe.set_adapters(["lora", "pixel"], adapter_weights=[1.0, 1.2])
    pipe.to(device="mps", dtype=torch.float16)
    return pipe


if __name__ == "__main__":
    # Create output directory if it doesn't exist
    os.makedirs(OUTPUT_DIRECTORY, exist_ok=True)

    # Read input
    prompt, num_images, resolution = read_input()
    pipe = init_pipe()

    # Settings
    name = prompt.replace(" ", "_").replace(",", "").replace(".", "").strip()
    prompt = f"pixel art, icon, {prompt}, simple, flat colors"
    negative_prompt = "3d render, realistic"

    # Generate images
    for i in range(num_images):
        img = pipe(
            prompt=prompt,
            negative_prompt=negative_prompt,
            num_inference_steps=8,
            guidance_scale=1.5,
        ).images[0]

        if resolution is not None:
            img = img.resize((resolution, resolution))

        filename = f"{name}-{i}.png"
        img.save(os.path.join(OUTPUT_DIRECTORY, filename))
