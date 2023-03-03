#!/usr/bin/python3
import re
import nltk
import sys
import getopt
import os
from collections import defaultdict, deque
import _pickle as pickle

BLOCK_SIZE = 1000
porter = nltk.PorterStemmer()

def usage():
    print("usage: " + sys.argv[0] + " -i directory-of-documents -d dictionary-file -p postings-file")

def build_index(in_dir, out_dict, out_postings):
    """
    build index from documents stored in the input directory,
    then output the dictionary file and postings file
    """
    print('indexing...')

    docs = os.listdir(in_dir)
    # sort by doc ids
    docs = sorted([int(doc) for doc in docs])
    
    # index documents 20 (BLOCK_SIZE) at a time
    for i in range(0, len(docs), BLOCK_SIZE):
        print(i)
        build_partial_index(in_dir, docs[i:i+BLOCK_SIZE], i // BLOCK_SIZE)

    # merge indexes
    merged_index = merge_all_indexes(len(docs) // BLOCK_SIZE + 1)

    # write to dictionary and postings
    with open(out_dict, 'w') as d, open(out_postings, 'w') as p:
        for i in range(len(merged_index)):
            word, lst = merged_index[i]
            d.write(word + ' ' + str(i) + '\n')
            p.write(str(lst) + '\n')


def build_partial_index(in_dir, docs, block_number):
    """
    build partial index of a block of documents
    """
    # keep a dictionary
    partial_index_dict = defaultdict(list)

    # go through each doc in the block
    for doc in docs:
        # tokenize
        f = open(os.path.join(in_dir, str(doc))).read()
        tokens = nltk.word_tokenize(f)

        # stem, casefold
        stemmed_tokens = [porter.stem(t).lower() for t in tokens]
        # get rid of punctuation/numbers
        final_tokens = [t for t in stemmed_tokens if t.isalpha()]

        # hash pairs into table
        for t in final_tokens:
            # only add doc to postings list if not already included
            if (not partial_index_dict[t]) or (partial_index_dict[t][-1] != doc):
                partial_index_dict[t].append(doc) 
    
    # sort index based on terms
    partial_index_list = list(partial_index_dict.items())
    partial_index_list.sort()

    # write block to file
    with open(f'{block_number}.pickle', 'wb') as block_file:
        pickle.dump(partial_index_list, block_file)


def merge_all_indexes(number_of_blocks):
    """
    two-way merge
    """
    def merge(a, b):
        i, j = 0, 0
        ans = []
        while i < len(a) and j < len(b):
            if a[i] < b[j]:
                ans.append(a[i])
                i += 1
            elif a[i] > b[j]:
                ans.append(b[j])
                j += 1
            else:
                ans.append(a[i])
                i += 1
                j += 1
        
        while i < len(a):
            ans.append(a[i])
            i += 1
        
        while j < len(b):
            ans.append(b[j])
            j += 1
        
        return ans

    def merge_two_indexes(index1, index2):
        final_index = []
        i, j = 0, 0
        while i < len(index1) and j < len(index2):
            if index1[i][0] < index2[j][0]:
                i += 1
            elif index1[i][0] > index2[j][0]:
                j += 1
            else:
                final_index.append((index1[i][0], merge(index1[i][1], index2[j][1])))
                i += 1
                j += 1

        while i < len(index1):
            final_index.append(index1[i])
            i += 1
        
        while j < len(index2):
            final_index.append(index2[j])
            j += 1
        
        return final_index

    # tuple of (filename, number)
    blocks = deque([str(n) for n in range(number_of_blocks)])

    while len(blocks) >= 2:
        block1 = blocks.popleft()
        block2 = blocks.popleft()

        # read and merge
        with open(block1 + '.pickle', 'rb') as block1_file, open(block2 + '.pickle', 'rb') as block2_file:
            # merge blocks
            result = merge_two_indexes(pickle.load(block1_file), pickle.load(block2_file))
            
            # write to new file
            result_block = block1 + '+' + block2
            with open(result_block + '.pickle', 'wb') as result_block_file:
                pickle.dump(result, result_block_file)
                blocks.append(result_block)
        
        # remove read files
        os.remove(block1 + '.pickle')
        os.remove(block2 + '.pickle')

    final_block = None
    # write the last file in dictionary and postings
    with open(blocks[0] + '.pickle', 'rb') as f:
        final_block = pickle.load(f)

    os.remove(blocks[0] + '.pickle')
    return final_block

input_directory = output_file_dictionary = output_file_postings = None

try:
    opts, args = getopt.getopt(sys.argv[1:], 'i:d:p:')
except getopt.GetoptError:
    usage()
    sys.exit(2)

for o, a in opts:
    if o == '-i': # input directory
        input_directory = a
    elif o == '-d': # dictionary file
        output_file_dictionary = a
    elif o == '-p': # postings file
        output_file_postings = a
    else:
        assert False, "unhandled option"

if input_directory == None or output_file_postings == None or output_file_dictionary == None:
    usage()
    sys.exit(2)

build_index(input_directory, output_file_dictionary, output_file_postings)
