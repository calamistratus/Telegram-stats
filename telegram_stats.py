import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

from IPython.display import clear_output

plt.style.use('https://github.com/dhaitz/matplotlib-stylesheets/raw/master/pitayasmoothie-dark.mplstyle')

INPUT_MESSAGE = '''Write the path to the directory containing the DataExport
If the input is "No", the current directory will be used.
The export folder is usually located at C:\\Users\\user\\Downloads\\Telegram Desktop ,the input should be in the same format\n'''

COMMANDS = '''
Chat Analysis Commands:
inspect : View messages from a specific chat
frequency : Show how active chats were over time
time : See when messages are sent most during the day
words : Count frequently used words with filtering options

Utility Commands:
analyze : View overall stats
username : Redo the username check
numbers : List available chat numbers
help : Show this command list
clear : Clean the output screen

Word List Commands (use words first):
random : Outputs a random selection of words
top : Lists the most common words
search : View the count of a specific words
stats : Misc word statistics
'''

def pick_from_path(path, filename):
    for i in os.listdir(path):
        if filename.lower() in i.lower():
            return os.path.join(path, i).replace('\\\\', '\\')
    else:
        raise Exception('File not found')

print(INPUT_MESSAGE)
while True:
    path = input().encode('unicode-escape').decode()
    try:
        if path.lower() == 'no' or path == '':
            path = pick_from_path(os.getcwd(), 'dataexport')
        else:
            path = pick_from_path(path, 'dataexport')
        try:
            path = pick_from_path(path, 'result')
            print('success!')
            break
        except:
            print('Chats were not downloaded')
    except:
        print('No DataExport in working derictory') if path.lower() == 'no' or path == '' else print('Invalid path')

json = pd.read_json(path).loc['list']

chats = json['chats'].copy()

try:
    chats.extend(json['left_chats'])
except:
    print('No left chats')

def get_messages(num, limit=None):
    if limit:
        return pd.DataFrame(chats[num]['messages'][:limit])
    else:
        return pd.DataFrame(chats[num]['messages'])

def save_graph(fig, name):
    save_the_plot = int(input('Do you want to save this plot? 0-No, 1-Yes'))
    if save_the_plot:
        path = input('Write the directory you want the picture to be saved in, current directory will be used otherwise')
        if path == '':
            path = os.getcwd()
        fig.savefig(os.path.join(path, name), dpi=200, bbox_inches='tight')

def input_loop(func):
    while True:
        try:
            return func()
        except:
            print('Invalid input')

def ask_num():
    return int(input('Write the chat number '))

def ask_hue():
    return int(input('Separate frequencies by user? 0-no, 1-yes '))

def check_username():
    usernames = []
    length = len(chats)
    for i in range(0, length, int(np.ceil(length/10))):
        if 'from' in get_messages(i).columns:
            if not get_messages(i)['from'] is pd.NA:
                usernames.extend(get_messages(i).iloc[:100]['from'].unique().tolist())

    username = pd.Series(usernames).value_counts().keys()[0]

    print('Is', username, 'your username?')
    answer = input('"Yes" or "(nothing)" if yes, input your username otherwise\n')
    if answer.lower() != 'yes' and answer:
        username = answer
    return username

def print_chat_numbers():
    print('\n Available chats:')
    for i in range(0, len(chats)):
        if 'from' in get_messages(i).columns:
            if not get_messages(i)['from'] is pd.NA:
                print(i, '|', ' | '.join([str(i) for i in get_messages(i, limit=100)['from'].unique() if str(i) != 'nan' and i != username]), '| ')
        else:
            print(i, '{', chats[i]['name'], '}')

def inspect(num, from_num, iter_count):
    messages = get_messages(num)
    index = from_num
    while True:
        for i in range(index, index + iter_count):
            if len(messages) > i:
                message = messages.loc[i]
                print('From:', message['from'], '|', 'At:', message['date'], '|', 'Number:', i, '\n', message['text'], '\n')
        if input('Write "Exit" to exit').lower() == 'exit':
            break
        index += iter_count
        clear_output()

def frequency(num, use_hue):
    messages = get_messages(num)
    fig = plt.figure(dpi=200, figsize=(15, 5))
    ax = fig.add_axes([0, 0, 1, 1])
    messages['date'] = pd.to_datetime(messages['date'])

    sns.kdeplot(data=messages, x='date', cut=0, hue='from' if use_hue else None, bw_adjust=.3, ax=ax)

    length = len(messages)
    messages_sent = [round((float(i) * length / 5)) * 5 for i in ax.get_yticks()]
    ax.set_yticks([i/length for i in messages_sent], messages_sent)
    ax.set_ylabel('Messages sent (per density unit)')

    max_date, min_date = messages['date'].max(), messages['date'].min()
    dates = np.arange(min_date, max_date + (max_date-min_date)/11, (max_date-min_date)/11)[:-1]
    ax.set_xticks(dates)
    ax.set_xlabel('Date')

    fig1 = plt.gcf()
    plt.show()

    save_graph(fig1, f'frequency_chat_number_{num}_usehue_{use_hue}.png')

def words(num, stopwords):
    def remove_marks(string):
        for i in (',', '.', '?', '&', '"', "'"):
            string = string.replace(i, '')
        return string

    texts = get_messages(num)['text'].str.lower().str.split()

    words = {}

    for i in texts:
        if i and type(i) != float:
            for j in i:
                j = remove_marks(j)
                if not j in words.keys():
                    words[j] = 0
                words[j] += 1
    words = pd.Series(words)
    stopword_set = set()
    match stopwords.lower():
        case 'en':
            from sklearn.feature_extraction._stop_words import ENGLISH_STOP_WORDS
            stopword_set = set(ENGLISH_STOP_WORDS)
        case 'ru':
            stopword_set = set(pd.read_json('stopwords-ru.json')[0])

    if stopword_set:
        words = words.drop(set(words.keys()).intersection(stopword_set))
    print('The word list is ready!')
    return words.sort_values(ascending=False)

def stats(words):
    lengths = pd.Series(words.keys()).apply(len)
    lengths_series = pd.Series([lengths.iloc[i] * words.iloc[i] for i in range(len(lengths))])
    print('Mean word appearence:', round(words.mean()), 'times')
    print('Median word appearence:', int(words.median()), 'wimes')
    print('Amount of one-time words:', words[words==1].sum())
    print('Amount of words used more than once:', words[words!=1].sum())
    print('Mean amount of letters in a word:', round(lengths.mean()))
    print('Median amount of letters in a word:', int(lengths.median()))
    print('Amount of words:', words.sum())
    print('Amount of letters:', lengths_series.sum())

def time(num, use_hue):
    def to_seconds(time):
        result = 0
        for i in range(3):
            result += int(time[i]) * (60 ** (2-i))
        return result

    messages = get_messages(num)
    fig = plt.figure(dpi=200, figsize=(15, 5))
    ax = fig.add_axes([0, 0, 1, 1])
    messages['date'] = pd.to_datetime(messages['date']).apply(lambda x: x.strftime('%H %M %S')).str.split().apply(to_seconds)

    sns.kdeplot(data=messages, x='date', cut=0, hue='from' if use_hue else None, bw_adjust=.3, ax=ax)

    ax.set_ylabel('Density of messages sent')

    dates = np.linspace(0, 24*60*60, 24)
    ax.set_xticks(dates, range(0,24))
    ax.set_xlabel('Hours')

    fig1 = plt.gcf()
    plt.show()

    save_graph(fig1, f'time_chat_number_{num}_usehue_{use_hue}.png')

def analyze():
    df = pd.DataFrame(chats)
    non_null_messages = df['messages'][df['messages'].apply(len) > 0]
    time_first = pd.to_datetime(non_null_messages.apply(lambda x: x[0]['date'] if len(x) > 0 else []))
    time_last = pd.to_datetime(non_null_messages.apply(lambda x: x[-1]['date'] if len(x) > 0 else []))
    lengths = non_null_messages.apply(len)
    print('Chats found:', len(chats))
    print('Which include:', df['type'].value_counts().to_string(), '\n')
    print('Earliest message:', time_first.min(), 'with chat number', time_first[time_first == time_first.min()].keys()[0])
    print('Latest message:', time_last.max(), 'with chat number', time_last.argmax())
    print('Most messages:', lengths.max(), 'with chat number', lengths.argmax())
    print('Least messages:', lengths.min(), 'with chat number', lengths.argmin())
    print('Mean amount of messages:', round(lengths.mean()))
    print('Median amount of messages:', int(lengths.median()))

username = check_username()
words_series = pd.Series()
clear_output()
print('Hello, ' + username + '!')
print(COMMANDS)
while True:
    match input().lower().strip():
        case 'exit':
            break

        case 'username':
            username = check_username()
            print('Hello, ' + username + '!')

        case 'help':
            print(COMMANDS)

        case 'clear':
            clear_output()

        case 'inspect':
            num = input_loop(ask_num)
            try:
                from_num = int(input(f'Write the number of start message (out of {len(get_messages(num))}) '))
            except:
                print('Invalid index or no messages')
                continue
            iter_count = input_loop(lambda: int(input('Write how many messages should be printed per iteration ')))
            inspect(num, from_num, iter_count)

        case 'numbers':
            print_chat_numbers()

        case 'frequency':
            num = input_loop(ask_num)
            use_hue = input_loop(ask_hue)
            frequency(num, use_hue)

        case 'time':
            num = input_loop(ask_num)
            use_hue = input_loop(ask_hue)
            time(num, use_hue)

        case 'words':
            num = input_loop(ask_num)
            stopwords = input('Write the stopword list which should be used: en-English, ru-Russian, none-No stopwords ')
            words_series = words(num, stopwords)

        case 'random':
            if len(words_series) > 0:
                amount = input_loop(lambda: int(input('Write how many words should be printed ')))
                print(words_series.sample(amount).to_string())
            else:
                print('Use "words" first')

        case 'top':
            if len(words_series) > 0:
                amount = input_loop(lambda: int(input('Write how many words should be printed ')))
                print(words_series.head(amount).to_string())
            else:
                print('Use "words" first')

        case 'search':
            if len(words_series) > 0:
                word = input('Write the word you want to search for ').lower()
                try:
                    print(word.title(), ':', words_series[word].to_string())
                    print(list(test.keys()).index(word), 'place')
                except:
                    print('Word not found, try without stopwords')
            else:
                print('Use "words" first')

        case 'stats':
            if len(words_series) > 0:
                stats(words_series)
            else:
                print('Use "words" first')

        case 'analyze':
            analyze()