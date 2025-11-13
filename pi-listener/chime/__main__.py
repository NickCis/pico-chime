if __name__ == '__main__':
    import argparse
    from .main import main
    from .constants import Port, BuzzerPin, Volume, Song

    parser = argparse.ArgumentParser(
        description="A simple CLI program that listens on a UDP port and plays a sound on a buzzer."
    )

    parser.add_argument(
        '--port',
        type=int,
        default=Port,
        help=f'UDP port to listen for broadcast messages (default: {Port})'
    )

    parser.add_argument(
        '--buzzer-pin',
        type=int,
        default=BuzzerPin,
        help=f'GPIO pin number that the buzzer is connected to (default: {BuzzerPin})'
    )

    def volume_type(value):
        f = float(value)
        if not (0.0 <= f <= 1.0):
            raise argparse.ArgumentTypeError("Volume must be between 0 and 1.")
        return f

    parser.add_argument(
        '--volume',
        type=volume_type,
        default=Volume,
        help=f'Volume for the song playback (0 to 1, default: {Volume})'
    )

    parser.add_argument(
        '--song',
        type=str,
        default=Song,
        help=f'The song that will be played (default: {Song})'
    )

    args = parser.parse_args()
    main(port=args.port, buzzer_pin=args.buzzer_pin,
         volume=args.volume, song_name=args.song)
