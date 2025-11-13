from time import sleep
from gpiozero import PWMOutputDevice


def sleep_ms(ms):
    sleep(ms / 1000)


def duration(tempo, t):
    # calculate the duration of a whole note in milliseconds (60s/tempo)*4 beats
    wholenote = (60000 / tempo) * 4

    # calculate the duration of the current note
    # (we need an integer without decimals, hence the // instead of /)
    if t > 0:
        note_duration = wholenote // t
    elif (t < 0):
        # dotted notes are represented with negative durations
        note_duration = wholenote // abs(t)
        note_duration *= 1.5  # increase their duration by a half

    return note_duration


class Player:
    def __init__(self, pin, volume=0):
        '''
        pin            # pin where buzzer is connected
        volume = 0.6   # set volume to a value between 0 and 1
        '''
        self.buzzer = PWMOutputDevice(pin=pin)
        self.volume = volume
        self.playing = False

    def playtone(self, freq):
        self.buzzer.value = self.volume
        self.buzzer.frequency = freq

    def be_quiet(self):
        self.buzzer.value = 0

    def playsong(self, song):
        if self.playing:
            return

        self.playing = True
        try:
            # name = song[0]
            tempo = song[1]  # get the tempo from the song

            # iterate over the notes of the melody.
            # Each note is a tuple (frequency, duration)
            for i in range(0, (len(song) - 2) // 2):
                frequency = song[2 + 2 * i]
                note_duration = int(duration(tempo, song[2 + 2 * i + 1]))

                if frequency == 0:  # REST
                    self.be_quiet()
                    sleep_ms(note_duration)
                else:
                    self.playtone(frequency)
                    # we only play the note for 90% of the duration
                    # and leave 10% as a pause between notes
                    note_duration_9 = int(note_duration * 0.9)
                    sleep_ms(note_duration_9)
                    self.be_quiet()
                    sleep_ms(note_duration - note_duration_9)
        except Exception as e:
            print('[music] error', e)
            self.be_quiet()
        self.playing = False
