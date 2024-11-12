import ffmpeg
import os
import math
from typing import Tuple, Optional
from tqdm import tqdm
import time

print("Setup Complete")


class TelegramVideoCompressor:
    def __init__(self) -> None:
        self.MAX_SIZE: int = 2147483648  # 2GB
        self.PRESET_RESOLUTIONS: dict = {
            "1080p": (1920, 1080),
            "720p": (1280, 720),
            "480p": (854, 480),
            "360p": (640, 360),
            "240p": (426, 240),
        }
        self.BITRATE_TIERS: dict = {1080: 1800, 720: 1024, 480: 750, 360: 500, 240: 250}

    def _get_video_info(self, input_path: str) -> dict:
        """Get video metadata using ffprobe"""
        try:
            probe = ffmpeg.probe(input_path)
            video_info = next(s for s in probe["streams"] if s["codec_type"] == "video")
            return video_info
        except ffmpeg.Error as e:
            raise Exception(f"Error reading video metadata: {str(e)}")

    def _calculate_target_resolution(self, width: int, height: int) -> Tuple[int, int]:
        """Calculate target resolution based on Telegram's scaling rules"""
        scale_factors = [(1280, 1280), (854, 848), (640, 640), (None, 432)]
        max_dimension = max(width, height)
        scale_factor = 1

        for threshold, factor in scale_factors:
            if threshold is None or max_dimension > threshold:
                scale_factor = factor / max_dimension
                break

        new_width = math.ceil(width * scale_factor / 2) * 2
        new_height = math.ceil(height * scale_factor / 2) * 2

        return new_width, new_height

    def _get_target_bitrate(
        self, width: int, height: int, original_bitrate: Optional[int] = None
    ) -> int:
        """Determine target bitrate based on resolution"""
        max_dimension = max(width, height)
        selected_tier = 360  # Default to lowest tier
        for tier in sorted(self.BITRATE_TIERS.keys()):
            if max_dimension >= tier:
                selected_tier = tier

        target_bitrate = self.BITRATE_TIERS[selected_tier] * 1024  # Convert to bps
        return (
            min(target_bitrate, original_bitrate)
            if original_bitrate
            else target_bitrate
        )

    def compress_video(
        self,
        input_path: str,
        output_path: str = None,
        target_resolution: Optional[str] = None,
        custom_resolution: Optional[Tuple[int, int]] = None,
        maintain_aspect_ratio: bool = True,
    ) -> None:
        """
        Compress video with specified resolution

        Args:
            input_path: Path to input video
            output_path: Path to save compressed video. If None, will use input_path with '_compressed' suffix
            target_resolution: String like '1080p', '720p', etc.
            custom_resolution: Tuple of (width, height) for custom resolution
            maintain_aspect_ratio: Whether to maintain aspect ratio when scaling
        """
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input file not found: {input_path}")

        # Generate default output path if none provided
        if output_path is None:
            filename, _ = os.path.splitext(input_path)
            output_path = f"{filename}_compressed.mp4"

        print("\nAnalyzing video...")
        video_info = self._get_video_info(input_path)
        original_width = int(video_info["width"])
        original_height = int(video_info["height"])

        # Determine target resolution
        if custom_resolution:
            target_width, target_height = custom_resolution
        elif target_resolution in self.PRESET_RESOLUTIONS:
            target_width, target_height = self.PRESET_RESOLUTIONS[target_resolution]
        else:
            target_width, target_height = self._calculate_target_resolution(
                original_width, original_height
            )

        # Maintain aspect ratio if requested
        if maintain_aspect_ratio:
            original_aspect = original_width / original_height
            target_aspect = target_width / target_height

            if original_aspect > target_aspect:
                target_height = int(target_width / original_aspect)
            else:
                target_width = int(target_height * original_aspect)

            target_width = (target_width // 2) * 2
            target_height = (target_height // 2) * 2

        print(f"\nTarget resolution: {target_width}x{target_height}")

        # Get bitrate
        original_bitrate = (
            int(video_info["bit_rate"]) if "bit_rate" in video_info else None
        )
        target_bitrate = self._get_target_bitrate(
            target_width, target_height, original_bitrate
        )

        # Compress video
        try:
            stream = ffmpeg.input(input_path)
            stream = ffmpeg.output(
                stream,
                output_path,
                vcodec="libx264",
                acodec="aac",
                video_bitrate=str(target_bitrate),
                audio_bitrate="128k",
                vf=f"scale={target_width}:{target_height}",
                preset="medium",
                crf="23",
                movflags="+faststart",
            )

            print("\nStarting compression...")
            process = ffmpeg.run_async(
                stream, pipe_stdout=True, pipe_stderr=True, overwrite_output=True
            )
            
            # Get video duration using ffprobe
            probe = ffmpeg.probe(input_path)
            duration = float(probe['streams'][0]['duration'])
            
            with tqdm(total=100, desc="Compressing", unit="%") as pbar:
                start_time = time.time()
                last_update = 0
                while process.poll() is None:
                    elapsed_time = time.time() - start_time
                    progress = min(100, (elapsed_time / duration) * 100)
                    # Only update if there's meaningful progress to avoid excessive updates
                    if progress - last_update >= 1:
                        pbar.update(progress - last_update)
                        last_update = progress
                    time.sleep(0.1)
                # Ensure we reach 100% at the end
                if last_update < 100:
                    pbar.update(100 - last_update)
                process.wait()
            print("Compression completed successfully!")

            # Print stats
            original_size = os.path.getsize(input_path)
            compressed_size = os.path.getsize(output_path)
            compression_percentage = (
                (original_size - compressed_size) / original_size
            ) * 100

            print(f"\nCompression Statistics:")
            print(f"Original file size: {original_size / (1024 * 1024):.2f} MB")
            print(f"Compressed file size: {compressed_size / (1024 * 1024):.2f} MB")
            print(
                f"Compression reduced the file size by: {compression_percentage:.2f}%"
            )

        except ffmpeg.Error as e:
            raise Exception(f"Error during video compression: {str(e)}")


# Example usage
def main() -> None:
    compressor = TelegramVideoCompressor()

    # Get input from user
    input_path = input("\nEnter the path to your video file: ")
    print("\nAvailable quality presets:")
    for preset in compressor.PRESET_RESOLUTIONS.keys():
        print(f"- {preset}")
    target_resolution = input("\nEnter desired quality (e.g. 720p): ")

    # Generate output path
    output_dir = "compressed"
    os.makedirs(output_dir, exist_ok=True)
    output_filename = f"compressed_{target_resolution}_{os.path.basename(input_path)}"
    base, _ = os.path.splitext(output_filename)
    output_path = os.path.join(output_dir, f"{base}.mp4")

    # Compress video
    compressor.compress_video(
        input_path=input_path,
        output_path=output_path,
        target_resolution=target_resolution,
    )


# Run the main function
if __name__ == "__main__":
    main()
