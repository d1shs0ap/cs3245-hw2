#!/usr/bin/python3
import re
import nltk
import sys
import getopt
import pickle

def usage():
    print("usage: " + sys.argv[0] + " -d dictionary-file -p postings-file -q file-of-queries -o output-file-of-results")

def run_search(dict_file, postings_file, queries_file, results_file):
    """
    using the given dictionary file and postings file,
    perform searching on the given queries file and output the results to a file
    """
    print('running search on the queries...')
    
    dictionary = []

    # open dictionary from dict_file
    with open(queries_file, 'r') as in_file, open(results_file, 'w') as out_file:
        full_results = []
        for query in in_file:
            query = query.rstrip()
            if(query == ""): 
                full_results.append('\n')
            else:
                postfix_query = infix_to_postfix(query.rstrip())
                full_results.append(evaluate_query(postfix_query, postings_file, dictionary))
        out_file.write('\n'.join(full_results))

def infix_to_postfix(query):
    stemmer = nltk.stem.porter.PorterStemmer()
    tokens = query.split()
    operator_stack = []
    output = []

    for token in tokens:
        if(token == 'NOT' or token == '('):
            operator_stack.append(token)
        elif(token == ')'):
            while(operator_stack[-1] != "(" and len(operator_stack) > 0):
                output.append(operator_stack.pop())  
        elif(token == 'OR'):
            while(len(operator_stack) > 0 and (operator_stack[-1] == 'NOT' or operator_stack[-1] == 'AND')):
                output.append(operator_stack.pop())
            operator_stack.append(token)
        elif(token == 'AND'):
            while(len(operator_stack) > 0 and operator_stack[-1] == 'NOT'):
                output.append(operator_stack.pop())
            operator_stack.append(token)   
            operator_stack.pop()   
        else:
            output.append(stemmer.stem(token.lower()))
    
    while len(operator_stack) > 0:
        output.append(operator_stack.pop())  

    return output

def evaluate_query(query, dictionary, postings_file):
    operands = []
    for i in range(len(query)):
        cur_token = query[i]
        if(cur_token != 'AND' and cur_token != 'OR' and cur_token != 'NOT'):
            operands.append(['term', cur_token])
        
        if(len(operands) > 0):
            intermediate = []
            op1 = operands.pop()
            if (cur_token == 'OR'):
                op2 = operands.pop()
                intermediate = eval_or(dictionary, postings_file, op1, op2)
            elif (cur_token == 'AND'):
                op2 = operands.pop()
                intermediate = eval_and(dictionary, postings_file, op1, op2)
            elif (cur_token == 'NOT'):
                if(i < len(query) and query[i+1] == 'AND' and len(operands) > 0):
                    i = i + 1
                    op2 = operands.pop()
                    intermediate = eval_and_not(dictionary, postings_file, op1, op2)
                else:
                    intermediate = eval_not(dictionary, postings_file, op1)
            operands.append(['list', intermediate])

    result = operands.pop()[1]
    return '\n'.join(result)

# query functions
def eval_or(dictionary, postings_file, op1, op2):
    list1 = get_postings(dictionary, postings_file, op1)
    list2 = get_postings(dictionary, postings_file, op2)
    i = 0
    j = 0
    res = []
    while i < len(list1) and j < len(list2):
        if list1[i] == list2[j]:
            res.append(list1[i])
            i += 1
            j += 1
        elif list1[i] < list2[j]:
            res.append(list1[i])
            i += 1
        else:
            res.append(list2[j])
            j += 1
    while i < len(list1):
        res.append(list1[i])
        i += 1
    while j < len(list2):
        res.append(list2[j])
        j += 1

    return ['list', res]

def eval_and(dictionary, postings_file, op1, op2):
    if(op1[0] == 'list' and op2[0] == 'list'):
        list1 = get_postings(dictionary, postings_file, op1)
        list2 = get_postings(dictionary, postings_file, op2)
        i = 0
        j = 0
        res = []
        while i < len(list1) and j < len(list2):
            if list1[i] == list2[j]:
                res.append(list1[i])
                i += 1
                j += 1
            elif list1[i] < list2[j]:
                while i < len(list1) and list1[i] < list2[j]:
                    i += 1
            else:
                while j < len(list2) and list1[i] > list2[j]:
                    j += 1
        return ['list', res]
            
    elif(op1[0] == 'list' and op2[1] == 'term'):
        

def eval_not(dictionary, postings_file, op):
    res = []
    op_list = get_postings(dictionary, postings_file, op)
    for x in doc_id_list:
        if x not in op_list:
            res.append(x)
    return ['list', res]

def eval_and_not(dictionary, postings_file, op1, op2):
    
def get_postings(dictionary, postings_file, op):
    if(op[0] == 'list'):
        return op[1]
    else:
        # todo

dictionary_file = postings_file = file_of_queries = output_file_of_results = None

try:
    opts, args = getopt.getopt(sys.argv[1:], 'd:p:q:o:')
except getopt.GetoptError:
    usage()
    sys.exit(2)

for o, a in opts:
    if o == '-d':
        dictionary_file  = a
    elif o == '-p':
        postings_file = a
    elif o == '-q':
        file_of_queries = a
    elif o == '-o':
        file_of_output = a
    else:
        assert False, "unhandled option"

if dictionary_file == None or postings_file == None or file_of_queries == None or file_of_output == None :
    usage()
    sys.exit(2)

run_search(dictionary_file, postings_file, file_of_queries, file_of_output)
