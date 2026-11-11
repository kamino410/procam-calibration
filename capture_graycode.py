import argparse
import sys
from pathlib import Path

import cv2


IMAGE_SUFFIXES = {'.bmp', '.jpeg', '.jpg', '.png', '.tif', '.tiff'}


def main():
    parser = argparse.ArgumentParser(
        description='Display gray-code patterns and capture an image for each one')
    parser.add_argument('pattern_dir', type=Path,
                        help='folder containing the gray-code pattern images')
    parser.add_argument('capture_number', type=int,
                        help='number used in the output folder (capture_<number>)')
    parser.add_argument('--camera-index', type=int, default=0,
                        help='OpenCV camera index (default: 0)')
    args = parser.parse_args()

    if args.capture_number < 0:
        parser.error('capture_number must be zero or greater')
    if not args.pattern_dir.is_dir():
        parser.error(f'pattern folder does not exist: {args.pattern_dir}')

    patterns = sorted(
        path for path in args.pattern_dir.iterdir()
        if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
    )
    if not patterns:
        parser.error(f'no supported images found in {args.pattern_dir}')
    if any(
        not path.stem.startswith('pattern_')
        or not path.stem[len('pattern_'):].isdigit()
        for path in patterns
    ):
        parser.error('pattern images must be named pattern_<index>.<extension>')

    output_dir = Path(f'capture_{args.capture_number}')
    if output_dir.exists():
        parser.error(f'output folder already exists: {output_dir}')

    camera = cv2.VideoCapture(args.camera_index)
    if not camera.isOpened():
        camera.release()
        parser.error(f'could not open camera index {args.camera_index}')

    try:
        output_dir.mkdir()
        window_name = 'Gray-code pattern'
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        print('Press SPACE to capture each pattern; press ESC or Q to stop.')

        for sequence_number, pattern_path in enumerate(patterns, start=1):
            pattern_index = pattern_path.stem[len('pattern_'):]
            pattern = cv2.imread(str(pattern_path), cv2.IMREAD_GRAYSCALE) #cv2.IMREAD_COLOR
            if pattern is None:
                print(f'Could not read pattern image: {pattern_path}', file=sys.stderr)
                return 1

            cv2.imshow(window_name, pattern)
            print(f'Pattern {sequence_number}/{len(patterns)}: {pattern_path}')

            while True:
                key = cv2.waitKey(0) & 0xFF
                if key in (27, ord('q')):
                    print('Capture stopped.')
                    return 0
                if key in (32, 13):
                    break

            ok, frame = camera.read()
            if not ok:
                print('Could not read a frame from the camera.', file=sys.stderr)
                return 1

            output_path = output_dir / f'graycode_{pattern_index}.png'
            if not cv2.imwrite(str(output_path), frame):
                print(f'Could not save captured image: {output_path}', file=sys.stderr)
                return 1
            print(f'Saved {output_path}')
    finally:
        camera.release()
        cv2.destroyAllWindows()

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
