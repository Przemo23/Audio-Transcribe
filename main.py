# importing libraries
import speech_recognition as sr

import os
import sys, getopt

from pydub import AudioSegment
from pydub.silence import split_on_silence
from pydub.silence import detect_silence


class Chunk:
    range = [0, 0]
    language = 'pl-PL'
    name = ''

    def __init__(self, range, language, name):
        self.range = range
        self.language = language
        self.name = name


# Define a function to normalize a chunk to a target amplitude.
def match_target_amplitude(aChunk, target_dBFS):
    ''' Normalize given audio chunk '''
    change_in_dBFS = target_dBFS - aChunk.dBFS
    return aChunk.apply_gain(change_in_dBFS)


def merge_small_chunks(chunks):
    merged_chunks = [chunks[0]]
    for i in range(1, len(chunks)):
        if chunks[i][1] - chunks[i][0] < 20000:
            merged_chunks[-1][1] = chunks[i][1]
        else:
            merged_chunks.append(chunks[i])
    return merged_chunks


def split_chunk_on_silence(audio):
    chunks_range = detect_silence(audio, 1000, -16)
    chunks_range = merge_small_chunks(chunks_range)

    chunks = [AudioSegment.silent(duration=10) + audio[chunk_range[0]:chunk_range[1]] + AudioSegment.silent(duration=10)
              for chunk_range in chunks_range]
    return chunks


def adjust_chunks_range(audio, chunks):
    for i in range(len(chunks) - 1):
        border_audio = audio[chunks[i].range[1] - 500:chunks[i].range[1] + 500]
        silence = detect_silence(border_audio, 600, -16)
        if len(silence) == 1:
            new_timestamp_offset = int(sum(silence[0]) / len(silence[0])) - 500
            if chunks[i + 1].range[0] == chunks[i].range[1]:
                chunks[i + 1].range[0] += new_timestamp_offset
            chunks[i].range[1] += new_timestamp_offset

    return chunks


# a function that splits the audio file into chunks
# and applies speech recognition

def silence_based_conversion(input_path, output_path, chunks_path):
    # open the audio file stored in
    # the local system as a wav file.
    audio = AudioSegment.from_wav(input_path)

    # open a file where we will concatenate
    # and store the recognized text
    fh = open(output_path, "w+")

    # split track where silence is 0.5 seconds
    # or more and get chunks
    chunks = parse_chunks(chunks_path)

    chunks = adjust_chunks_range(audio, chunks)

    # create a directory to store the audio chunks.
    try:
        os.mkdir('audio_chunks')
    except FileExistsError:
        pass

    # move into the directory to
    # store the audio files.
    os.chdir('audio_chunks')

    i = 0
    # process each chunk
    for chunk in chunks:
        normalized_chunk = match_target_amplitude(audio[chunk.range[0]:chunk.range[1]], -20.0)

        sub_chunks = split_chunk_on_silence(normalized_chunk)

        fh.write(chunk.name + '\n\n')

        for sub_chunk in sub_chunks:

            # export audio chunk and save it in
            # the current directory.
            print("saving chunk{0}.wav".format(i))
            # specify the bitrate to be 192 k
            sub_chunk.export("./chunk{0}.wav".format(i), bitrate='192k', format="wav")

            # the name of the newly created chunk
            filename = 'chunk' + str(i) + '.wav'

            print("Processing chunk " + str(i))

            # get the name of the newly created chunk
            # in the AUDIO_FILE variable for later use.
            file = filename

            # create a speech recognition object
            r = sr.Recognizer()

            # recognize the chunk
            with sr.AudioFile(file) as source:
                # remove this if it is not working
                # correctly.
                r.adjust_for_ambient_noise(source)
                audio_listened = r.listen(source)

            try:
                # try converting it to text
                rec = r.recognize_google(audio_listened, language=chunk.language)
                # write the output to the file.
                fh.write(rec + ". " + '\n')

            # catch any errors.
            except sr.UnknownValueError:
                print("Could not understand audio")

            except sr.RequestError as e:
                print("Could not request results. check your internet connection")

            i += 1

    os.chdir('..')


def parse_chunks(path):
    # Read the file
    file = open(path, 'r')
    lines = file.readlines()

    chunks = []

    # Extract range, language and name
    for line in lines:
        chunks.append(create_chunk(line))

    return chunks


def create_chunk(line):
    # Create a chunk object from a line of the chunk_file
    chunk_data = line.split()

    # Extract range from string
    range_str = chunk_data[0].split('-')
    start_time = range_str[0].split(':')
    end_time = range_str[1].split(':')
    chunk_range = [(int(start_time[0]) * 60 + int(start_time[1])) * 1000,
                   (int(end_time[0]) * 60 + int(end_time[1])) * 1000]

    # Extract language and name if they exist
    if len(chunk_data) > 1:
        language = chunk_data[1]
    if len(chunk_data) > 2:
        name = chunk_data[2]

    return Chunk(chunk_range, language, name)


def main(argv):
    infile = ''
    outfile = ''
    chunks = ''

    try:
        opts, args = getopt.getopt(argv, "i:o:c:", ["input=", "output=", "chunks="])
    except getopt.GetoptError:
        print('Invalid arguments')
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-i", "--input"):
            infile = arg
        elif opt in ("-o", "--output"):
            outfile = arg
        elif opt in ("-o", "--chunks"):
            chunks = arg
    if infile == '' or outfile == '':
        print('You need to specify the input and output files')
        sys.exit(1)

    silence_based_conversion(infile, outfile, chunks)


if __name__ == "__main__":
    main(sys.argv[1:])
