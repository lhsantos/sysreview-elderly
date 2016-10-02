import sys
import os
import codecs
import argparse
import bibtexparser as bibp
import bibtexparser.customization as bibp_cust
import re


def is_valid_dir(parser, arg):
    if not os.path.exists(arg):
        parser.error("the directory %s does not exist!" % arg)
    else:
        return arg


def is_valid_file(parser, arg):
    if not os.path.exists(arg):
        parser.error("the file %s does not exist!" % arg)
    else:
        return codecs.open(arg, 'r', encoding='utf-8')


# process command line
arg_parser = argparse.ArgumentParser(description='Merges one or more BibTex files, removing duplicates.')
arg_parser.add_argument('-o', '--output', type=argparse.FileType('w'), default='out.bib', help='output file')
arg_parser.add_argument('-a', '--aux-dir', type= lambda x: is_valid_dir(arg_parser, x), default='.', help='auxiliary directory')
arg_parser.add_argument('-i', '--disable-ignored', type=bool, default=False, help='disable generating ignored entries database')
arg_parser.add_argument('-d', '--disable-duplicates', type=bool, default=False, help='disable generating duplicate entries database')
arg_parser.add_argument('input', type= lambda x: is_valid_file(arg_parser, x), nargs='+', help='input file')
args = arg_parser.parse_args()


# converts a field value (title, author) to a standard representation
def normalize(str):
    patterns = {
        '^[\\s\\-:\\"\']+' : '',
        '[\\s\\-:\\"\']+$' : '',
        '[\\s\\-:\\"\']+' : '_',
    }
    for pattern, new_value in patterns.items():
        str = re.sub(pattern, new_value, str)
    return str.lower()


# given an array of author names, generate a unique key for those authors
def gen_authors_key(authors):
    key = []
    for author in authors:
        # takes the author last name, normalizes it and appends to the vector
        key.append(normalize(author.split(',')[0]))
    key.sort()
    return ','.join(key)



# compares the given field between two entries and returns -1, 0, 1
# according to the amount of information
def compare_field(entry_a, entry_b, field):
    val_a = 0
    if field in entry_a:
        val_a = len(entry_a[field])
    val_b = 0
    if field in entry_b:
        val_b = len(entry_b[field])
    return -1 if val_a < val_b else (1 if val_a > val_b else 0)


# given 2 bib entries, picks the one who seems to have more information
def pick(entry_a, entry_b):
    comp = compare_field(entry_a, entry_b, 'abstract')
    if (comp == 0):
        comp = compare_field(entry_a, entry_b, 'keyword')
    if (comp == 0):
        comp = compare_field(entry_a, entry_b, 'booktitle')
    if comp >= 0:
        return entry_a, entry_b
    else:
        return entry_b, entry_a


# main duplicates checking logic
# all entries are indexed by a normalized key formed by author names
# if two entries have the same authors key, they are further checked for field equality
# if two entries are considered equal, then the entry that seems to have more information
# is picked
def check_duplicate(merged, duplicates_db, authors_index, source, new_entry):
    authors_key = gen_authors_key(new_entry['author'])
    new_entry['note'] = u'from: ' + source
    if authors_key not in authors_index:
        authors_index[authors_key] = dict()
    
    # looks up the entry dictionary for this combination of authors
    authors_entries = authors_index[authors_key]
    new_title = normalize(new_entry['title'])
    final_title = new_title
    final_entry = new_entry
    for cur_title, cur_id in authors_entries.items():
        # are the titles very close to each other?
        if cur_title == new_title:
            final_title = cur_title
            final_entry, duplicate = pick(merged[cur_id], new_entry)
            del merged[cur_id]
            duplicate['note'] = u''.join(['duplicate of: ', final_entry['note'][len('from: '):], ' -- ', final_entry['ID']])
            duplicates_db.entries.append(duplicate)
            break

    # stores the picked entry, preventing id clash
    final_id = final_entry['ID']
    while final_id in merged:
        final_id = final_id + '_'
        final_entry['ID'] = final_id
    merged[final_id] = final_entry
    authors_entries[final_title] = final_id


# saves an auxiliary database to an output file whose name is
# the given input file base name + a suffix + original extension or ".bib"
def save_aux_bib(db, input_file_name, suffix):
    parts = os.path.splitext(input_file_name);
    out_file_name = "".join([parts[0], '-', suffix, (parts[1] if parts[1] else '.bib')])
    try:
        for entry in db.entries:
            if 'author' in entry:
                entry['author'] = ' and '.join(entry['author'])
        out = bibp.dumps(db).encode('utf-8')
        with open(os.path.join(args.aux_dir, out_file_name), 'w') as out_file:
            out_file.write(out)
    except:
        print("failed to write output file '" + out_file_name + "'", sys.exc_info()[0])


# customization for each record
# uses unicode; convert authors string to array of 'Last, First' strings; and uses double dashes for page ranges
def process_entry(record):
    for key in record:
        if isinstance(record[key], str):
            record[key] = record[key].decode(encoding='ascii', errors='ignore').encode('utf-8')
    record = bibp_cust.convert_to_unicode(record)
    record = bibp_cust.author(record)
    record = bibp_cust.page_double_hyphen(record)
    return record


# creates the BibTex parser
bib_parser = bibp.bparser.BibTexParser()
bib_parser.customization = process_entry 

# prepares auxiliary objects
writer = bibp.bwriter.BibTexWriter()
merged = dict()
authors_index = dict()

# processes the input files
for input_file in args.input:
    # loads the source database and creates empty ignored, duplicates databases
    db = bibp.load(input_file, parser=bib_parser)
    ignored_db = bibp.bibdatabase.BibDatabase()
    duplicates_db = bibp.bibdatabase.BibDatabase()
    
    # processes each entry
    for entry in db.entries:
        if 'author' not in entry:
            ignored_db.entries.append(entry)
            continue
        check_duplicate(merged, duplicates_db, authors_index, os.path.basename(input_file.name), entry)

    # if that's the case, saves the ignored, duplicates databases
    if not args.disable_ignored:
        save_aux_bib(ignored_db, input_file.name, 'ignored')
    if not args.disable_duplicates:
        save_aux_bib(duplicates_db, input_file.name, 'duplicates')

# saves the final database
db = bibp.bibdatabase.BibDatabase()
for entry in merged.values():
    entry['author'] = ' and '.join(entry['author'])
    db.entries.append(entry)
out = bibp.dumps(db).encode('utf-8')
args.output.write(out)
