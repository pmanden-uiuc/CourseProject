import pandas as pd
import nltk
nltk.download('punkt')
from sklearn.feature_extraction.text import CountVectorizer
import random
import re

#
# Removes whitespace, unnecessary words from the provided url and returns
# a space separated string
#
def tokenize_url(url):
    url = url.strip('\n')

    word_list = re.split('[/.:]', url)
    unwanted = {'', 'https', 'http', 'www'}
    word_list = [e for e in word_list if e not in unwanted]

    if len(word_list) > 0:
        return (' '.join(word_list))
    else:
        return ''

#
# Loads the specified file (each line a document), tokenizes each line, and returns
# list of specified number of items
#
def load_file(filename, no_items, random_selection=True):
    file_handle = open(filename, "r")

    term_doc_list = []
    while True:
        line = file_handle.readline()

        if not line:
            break
        tokens = tokenize_url(line)
        if len(tokens) > 0:
            term_doc_list.append(tokens)

    file_handle.close()

    if random_selection == True:
        ret_list = random.sample(term_doc_list, no_items)
    else:
        ret_list = term_doc_list[0:no_items-1]

    return ret_list

#
# Loads test data from the specified file and returns a list of documents (doc per line)
# (No processing done)
#
def load_test_samples(filename, start_loc, no_samples=100):
    file_handle = open(filename, "r")

    sample_list = []
    line_index = 0
    lines_copied = 0
    while True:
        line = file_handle.readline()

        if not line:
            break
        line_index += 1

        if line_index >= start_loc:
            sample_list.append(line)
            lines_copied += 1
            if lines_copied >= no_samples:
                break

    file_handle.close()
    return(sample_list)

#
# Generates term document matrix from the provided list of docs. Input is expected to be a list
# with each line representing a doc. Each line is a list of space separated terms
# Returns
#   - tdm: Term doc matrix
#   - freq: A dictionary of terms and corresponding counts
#   - total_features: number of terms in all docs
#   - total_cnts_features : Count of each term in tdm
#
def calc_term_doc_matrix(docs):
    vec = CountVectorizer()
    X = vec.fit_transform(docs)
    total_features = len(vec.get_feature_names())

    tdm = pd.DataFrame(X.toarray(), columns=vec.get_feature_names())

    word_list = vec.get_feature_names();
    count_list = X.toarray().sum(axis=0)
    total_cnts_features = count_list.sum(axis=0)
    freq = dict(zip(word_list, count_list))

    return tdm, freq, total_features, total_cnts_features

#
# Returns a list of probability of words in the given class
#
def get_probability_with_laplace_smoothing(url, freq, total_cnts_features, total_features):

    combined_prob = 1.0
    prob_s_with_ls = []
    new_word_list = tokenize_url(url)
    new_word_list = new_word_list.split(' ')

    for word in new_word_list:
        if word in freq.keys():
            count = freq[word]
        else:
            count = 0

        word_prob = ((count + 1) / (total_cnts_features + total_features))
        combined_prob = combined_prob * word_prob

        prob_s_with_ls.append(word_prob)

    prob = dict(zip(new_word_list, prob_s_with_ls))
    return prob, combined_prob

class naive_bayes_classifier():
    def __init__(self, pos_training_data_file_, neg_training_data_file_, no_training_samples_):
        self.pos_training_data_file = pos_training_data_file_
        self.neg_training_data_file = neg_training_data_file_
        self.no_training_samples = no_training_samples_

    def initialize_classifier(self):
        # Load positive training data
        docs = load_file(self.pos_training_data_file, self.no_training_samples)

        # Calculate term document matrix, term frequency, no of terms, total number of all terms
        pos_tdm, pos_freq, pos_total_features, pos_total_cnts_features = calc_term_doc_matrix(docs)

        # Load negative training data
        docs = load_file(self.neg_training_data_file, self.no_training_samples)

        # Calculate term document matrix, term frequency, no of terms, total number of all terms
        neg_tdm, neg_freq, neg_total_features, neg_total_cnts_features = calc_term_doc_matrix(docs)

        # Calculate size of vocabulary (positive & negative)
        pos_features = pos_tdm.columns.tolist()
        neg_features = neg_tdm.columns.tolist()
        total_features = len(set(pos_features + neg_features))

        self.pos_freq = pos_freq
        self.pos_total_cnts_features = pos_total_cnts_features
        self.neg_freq = neg_freq
        self.neg_total_cnts_features = neg_total_cnts_features
        self.total_features = total_features

    #
    # Classifies the provided URL as positive or negative.
    # Returns 'True' for positive classification, 'False' for negative classification
    #
    def classify(self, test_url):
        pos_words_prob, pos_combined_word_prob = \
            get_probability_with_laplace_smoothing(test_url,
                self.pos_freq, self.pos_total_cnts_features, self.total_features)

        neg_words_prob, neg_combined_word_prob = \
            get_probability_with_laplace_smoothing(test_url,
                self.neg_freq, self.neg_total_cnts_features, self.total_features)

        if pos_combined_word_prob > neg_combined_word_prob:
            #print("{} categorized as Positive".format(test_url))
            return True
        else:
            #print("{} categorized as Negative".format(test_url))
            return False

def test_naive_bayes_classifier(pos_training_data_file, neg_training_data_file,
                                no_training_samples, no_test_samples):

    classifier = naive_bayes_classifier(pos_training_data_file, neg_training_data_file,
                                        no_training_samples)
    classifier.initialize_classifier()

    # load positive & negative test samples. Test samples are selected from the same input files, however,
    # samples are selected from beyond the no_training_samples to avoid using data used for training.
    # (see load_test_samples function)
    pos_test_samples = load_test_samples(pos_training_data_file, no_training_samples, no_test_samples)
    neg_test_samples = load_test_samples(neg_training_data_file, no_training_samples, no_test_samples)

    true_positive = 0
    true_negative = 0

    # Test against positive samples
    for test_url in pos_test_samples:
        result = classifier.classify(test_url)
        if result == True:
            true_positive += 1
        else:
            print("{} False Negative".format(test_url))

    # test against negative samples
    for test_url in neg_test_samples:
        result = classifier.classify(test_url)
        if result == True:
            print("{} is False Positive".format(test_url))
        else:
            true_negative += 1

    print('Positive Samples {}, Accuracy - {:.2}'.format(true_positive, true_positive/no_test_samples))
    print('Negative Samples {}, Accuracy - {:.2}'.format(true_negative, true_negative/no_test_samples))

    precision = true_positive/(true_positive+no_test_samples-true_negative)
    recall = true_positive/(true_positive+no_test_samples-true_positive)

    print('Precision {:.2}'.format(precision))
    print('Recall    {:.2}'.format(recall))
    print('F1 score  {:.2}'.format(2*precision*recall/(precision+recall)))


if __name__ == '__main__':
    #pos_training_data_file = 'directory-positives.txt'
    #neg_training_data_file = 'directory-negatives.txt'
    #no_training_samples = 800
    #no_test_samples = 100

    # Test directory classifier
    test_naive_bayes_classifier('directory-positives.txt', 'directory-negatives.txt', 800, 100 )

    # Test faculty classifier
    test_naive_bayes_classifier('faculty-pages-positives.txt', 'faculty-pages-negatives.txt', 6000, 300)


