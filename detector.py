import os
import sys
from graph import Graph
from nltk.corpus import wordnet as wn

class Detector:
    """
    Main program class

    Reads a directory, organizes its contents
    into a graph and detects plagiarism
    """

    def __init__(self, directory, sequence_size = 5, num_sequences = 10):
        """
        >>> det = Detector("/test_essays", 6, 18)
        >>> det.directory
        '/test_essays'
        >>> det.sequence_size
        6
        >>> det.num_sequences
        18
        """

        # read attritbutes
        self._directory = directory
        # add a dot to beginnig of file path
        if directory[0] != ".":
            directory = "." + directory
            
        self._sequence_size = sequence_size
        self._num_sequences = num_sequences

        self._docs_dict = self.create_docs_dict(directory)


    def run_detection(self, flag):
        """
        Runs the detection and returns a list of tuples
        of possible plagiarisms

        flag determines algorithm:
        1 = same_sentences
        """

        if flag == 1:
            return self.same_sentences()
        elif flag == 2:
            return self.common_sequences()




    @property
    def directory(self):
        return self._directory

    @property
    def sequence_size(self):
        return self._sequence_size

    @property
    def num_sequences(self):
        return self._num_sequences

    @property
    def docs_dict(self):
        return self._docs_dict


    # 1st algorithm

    def same_sentences(self):
        """
        Tries to find plagiarized documents by finding sentences
        in common

        Simplest algorithm
        """
        
        # split each document in the dict
        # into sentences (split by punctuation marks)
        docs_dict = self.split_docs_into_sentences()

        # create a graph for the docs and 
        # add all docnames as vertices
        doc_graph = Graph(set(docs_dict.keys()))

        # find number of sentences in common
        # and add the numbers as edges

        docnames_list = list(doc_graph.vertices())
        for i, v1 in enumerate(docnames_list):
            for v2 in docnames_list[i+1:]:
                # each vertex is compared only to 
                # its subsequent vertices in the list,
                # to avoid double-computing

                sentences_in_common = 0
                sentences_in_2 = set(docs_dict[v2])

                for sentence_in_1 in docs_dict[v1]:
                    if sentence_in_1 in sentences_in_2:
                        sentences_in_common += 1

                if sentences_in_common >= num_sequences:
                    doc_graph.add_edge((v1,v2), sentences_in_common)

        # return list of edges in decreasing order of sentences in common
        return sorted(doc_graph.edges(), key = doc_graph.edges().get, reverse = True)

    def create_docs_dict(self, directory):
        """
        reads the directory and returns a dict
        with filenames as keys and files (as strings)
        as values
        """
        filenames = os.listdir(directory)
        docs_dict = {}

        for fh in filenames:
            path = directory + "/" + fh
            curr_file = open(path, "rb")

            docs_dict[fh] = str(curr_file.read())

            curr_file.close()

        return docs_dict

    def split_docs_into_sentences(self):
        """
        Splits all the document files inside 
        the dictionary into sentences
        """

        filenames = self._docs_dict.keys()
        split_dict = {}

        for fl in filenames:
            filestring = self._docs_dict[fl]
            split_file = self.break_into_sentences(filestring)
            split_dict[fl] = split_file

        return split_dict

    def break_into_sentences(self, s, into_words = False):
        """
        Separte the file strings into sentences
        (strings delimitated by punctuation)
        e.g.:

        'Hello, world' -> ['Hello', ' world']

        >>> det = Detector("/test_essays", 6, 18)
        >>> det.break_into_sentences('Hello, world')
        ['Hello', ' world']
        >>> det.break_into_sentences('Str, to. test; breaking? function')
        ['Str', ' to', ' test', ' breaking', ' function']
        >>> det.break_into_sentences('Str to test; breaking function?', True)
        ['Str', 'to', 'test', 'breaking', 'function']

        """
        punctuation = set([",", ".", ";", "!", "?", "\n", "\t"])

        if into_words:
            # if this flag is set, break string
            # into words instead of sentences
            # to do that, separate by spaces as well
            punctuation.add(" ")

        #return list
        ret = []

        curr_sentence = ""

        for c in s:

            if c in punctuation:
                if curr_sentence != "":
                    # add sentence to return list
                    # and reset current sentence
                    ret.append(curr_sentence)
                    curr_sentence = ""
            else:
                # add character to sentence
                curr_sentence += c

        #after loop, add last sentence
        if curr_sentence != "":
            ret.append(curr_sentence)

        return ret


    # 2nd Algorithm

    def common_sequences(self):
        """
        Find the pairs of documents that have
        sequences in common of size n or
        greater (where n was determined by the user)

        Each pair of documents gets a score equal to the sum of the 
        lengths of the common sequences
        """

        docnames_list = list(self._docs_dict.keys())

        docs_dict = self._docs_dict
        doc_graph = Graph(set(docnames_list))

        for i, v1 in enumerate(docnames_list):
            for v2 in docnames_list[i+1:]:
                # each vertex is compared only to 
                # its subsequent vertices in the list,
                # to avoid double-computing
                print("pair : ",v1,v2)
                nbr = self.common_sequences_score(docs_dict[v1],docs_dict[v2],self._sequence_size)
                print("score: ",nbr)
                if nbr > 0:
                    doc_graph.add_edge((v1,v2), nbr)

        # return list of edges in decreasing order of sequences in common
        return sorted(doc_graph.edges(), key = doc_graph.edges().get, reverse = True)

    def common_sequences_score(self,l1,l2,size=0):
        """
        Finds how many substrings 
        are common between 2 strings
        and gives a score equal to the sum of the lengths
        of these common substrings
        
        Only substrings greater or equal to 'size' are counted

        O( len(l1) * len(l2) )

        """

        memo = {}
        nbr = 0
        print("got into common_sequences_score")

        # the longest common substring starting at l1[i] and l2[j] has length:
        # 1) 0, if l1[i] != l2[j]
        # 2) 1 + length of longest common substring starting at l1[i+1] and l2[j+1]
        # This property will be used to find lengths of all common substrings bigger or equal
        # to 'size'

        # go through all pairs i,j starting at the ends of the strings
        for i in range(len(l1))[::-1]:
            for j in range(len(l2))[::-1]:
                # only add non-zero elements to memo
                # to save memory
                if l1[i] == l2[j]:
                    if (i+1,j+1) in memo:
                        memo[(i,j)] = 1 + memo[(i+1,j+1)]
                    else:
                        memo[(i,j)] = 1

                # if l1[i-1] and l2[j-1] exist and are different,
                # then the common substring starting at (i,j)
                # is a substring of l1 and l2, but not part
                # of any other common substring

                # Add its length to score if it's above
                # the size threshold
                if i == 0 or j == 0 or l1[i-1] != l2[j-1]:
                    if (i,j) in memo and memo[(i,j)] >= size:
                        nbr += memo[(i,j)]
                        print("nbr so far", nbr)

        return nbr

    # 3rd Algorithm

    # 4th Algorithm
    
    def get_similar_words(word):
        """
        Returns similar words to a given word,
        using the WordNet database
        """
        # get entry in database closest to word
        entry = wn.synsets(word)[0]

        # get hypernyms and hyponyms
        similars = entry.hypernyms() + entry.hyponyms()

        # go through similars and clean the list
        return_ls = list()
        for s in similars:
            name = s.name()

            # remove info about the entry
            # e.g. bottle.n.01 -> bottle
            name = name[:name.find(".")]

            # remove underscores
            name = name.replace("_", " ")

            # remove entries that contain the word itself
            # e.g. bottle -> wine_bottle
            if not word in name:
                return_ls.append(name)

        return return_ls



            



# end of Detector definition

if __name__=="__main__":
    import doctest
    doctest.testmod()
