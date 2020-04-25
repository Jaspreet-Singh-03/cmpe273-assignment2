from flask import Flask, request, jsonify, send_from_directory, json
import sqlite3
import os
# import pytesseract

Solution = Flask(__name__)
Solution.config['STATIC_FOLDER'] = 'files'
files_folder = os.path.join(Solution.root_path, Solution.config['STATIC_FOLDER'])


def create_databases():
    conn = sqlite3.connect('scantron.db')
    #   conn.execute('DROP TABLE IF EXISTS SCANTRON_DB')
    #   conn.execute('DROP TABLE IF EXISTS ANSWER_KEY_DB')

    conn.execute('''CREATE TABLE IF NOT EXISTS ANSWER_KEY_DB
                  (TEST_ID     INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                  SUBJECT      TEXT    UNIQUE    NOT NULL,
                  ANSWER_KEY   TEXT    NOT NULL)   ;''')

    conn.execute('''CREATE TABLE IF NOT EXISTS SCANTRON_DB
               (SCANTRON_ID INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
               NAME         TEXT     NOT NULL,
               SUBJECT_ID   INT      NOT NULL,
               SUBJECT      TEXT     NOT NULL,
               ANSWER_KEY   TEXT NOT NULL,
               FOREIGN KEY (SUBJECT_ID) REFERENCES ANSWER_KEY_DB (TEST_ID) )  ;''')
    print("Table created successfully")
    conn.close()


##############################GET JSON SCANTRON FILE################################
@Solution.route('/files/<path:path>')
def send_file_at_path(path):
    try:
        return send_from_directory('files', path)
    except Exception as e:
        return f'Exception : File {path} {e} '


####################################################################################


#################################CREATE TEST########################################
@Solution.route('/api/tests', methods=["POST"])
def create_test():
    record = request.get_json()
    subject_name = record.get('subject')
    answer_keys = record.get('answer_keys')

    data = {'subject': subject_name, 'answer_keys': transform_key(answer_keys)}
    test_id = insert_test_record(data)

    response = dict()
    if isinstance(test_id, int):
        response['test_id'] = test_id
        response['subject'] = subject_name
        response['answer_keys'] = answer_keys
        return jsonify(response), 201
    else:
        return test_id


def insert_test_record(item):
    row_id = int()
    subject = item['subject']
    answer_keys = item['answer_keys']
    try:
        conn = sqlite3.connect('scantron.db')
        conn.execute("INSERT INTO ANSWER_KEY_DB (SUBJECT,ANSWER_KEY) VALUES ( ? , ? )", (subject, answer_keys))
        cursor = conn.execute('SELECT last_insert_rowid() from ANSWER_KEY_DB')
        for row in cursor:
            row_id = int(row[0])
        conn.commit()
        conn.close()
        return row_id

    except sqlite3.Error as e:
        return "Database Error %s" % e


###################################################################

def transform_key(test_key):
    ans_key = ""
    for key in test_key:
        if len(test_key[key]) == 1:
            ans_key = ans_key + key + ":" + test_key[key] + "|"
        else:
            ans_key = ans_key + key + ":" + "Wrong Input" + "|"

    return ans_key


def retransform_key(test_key):
    ans_key = dict()
    try:
        split_list = test_key.split("|")
        for element in split_list:
            if element:
                index = element.split(":")
                key = index[0]
                val = index[1]
                ans_key[key] = val
        return ans_key
    except Exception :
        return None


#########################VIEW ALL TESTS################################
@Solution.route('/api/tests', methods=["GET"])
def view_all_tests():
    records = view_all_test_record()
    return jsonify(records)


def view_all_test_record():
    record_list = list()
    conn = sqlite3.connect('scantron.db')
    # QUERY for Viewing All the records and TEST ID's
    cursor = conn.execute("SELECT TEST_ID, SUBJECT, ANSWER_KEY from ANSWER_KEY_DB")
    for row in cursor:
        item = dict()
        item["test_id"] = row[0]
        item["subject"] = row[1]
        item["answer_keys"] = retransform_key(row[2])
        record_list.append(item)
    conn.close()
    return record_list


###################################################################


################################UPLOAD SCANTRON###################################
@Solution.route('/api/tests/<int:subject_id>/scantrons', methods=["POST"])
def upload_scantron(subject_id):
    subject_name, answer_keys = get_subject_details(subject_id)

    if not subject_name:
        return "Couldn't insert record, no test subject created yet"
    else:
        try:
            file = request.get_data().decode()
            if not file:
                return "No file is uploaded, please upload the file"
            else:
                record = json.loads(file)

            response = dict()
            user_name = record.get('name')
            user_subject = record.get('subject')
            user_key = record.get('answers')
            if subject_name.lower() == user_subject.lower():
                data = {'name': user_name, 'subject': subject_name, 'subject_id': subject_id,
                        'answers': transform_key(user_key)}
                scores = calculate_score(data['answers'], answer_keys)
                if scores is not None:
                    scantron_id = insert_scantron_record(data)
                    response['scantron_id'] = scantron_id
                    response['scantron_url'] = "http://localhost:5000/files/scantron-" + str(scantron_id) + ".json"
                    response['name'] = data['name']
                    response['subject'] = data['subject']
                    response['score'] = scores['score']
                    response['result'] = scores['result']
                    filename = 'scantron-%s.json' % str(scantron_id)
                    #                   file_content = { "name" : user_name, "subject": user_subject, "answers": user_key}
                    with open((os.path.join(files_folder, filename)), 'w') as file:
                        file.write(json.dumps(record))
                        file.close()

                    return jsonify(response), 201
                else:
                    return "Submitted Answer key has different length than test answer key , please check"
            else:
                return f"Subject name {user_subject} is not in record , did you mean {subject_name} with test_id {subject_id}"
        except Exception as e:
            return "Exception occured %s" % e


def insert_scantron_record(item):
    #   id = item['scantron_id'];  url = item['scantron_url'];
    name = item['name']
    sub = item['subject']
    sub_id = item['subject_id']
    key = item['answers']
    conn = sqlite3.connect('scantron.db')
    conn.execute("INSERT INTO SCANTRON_DB (NAME,SUBJECT_ID,SUBJECT,ANSWER_KEY) VALUES ( ? , ? , ? , ? )",
                 (name, sub_id, sub, key))
    row_id = int()
    cursor = conn.execute('SELECT last_insert_rowid() from SCANTRON_DB')
    for row in cursor:
        row_id = int(row[0])
    conn.commit()
    conn.close()
    return row_id


def get_subject_details(test_id):
    conn = sqlite3.connect('scantron.db')
    cursor = conn.execute("SELECT SUBJECT,ANSWER_KEY from ANSWER_KEY_DB where TEST_ID=?", (test_id,))
    subject_name = None
    answer_keys = None
    for row in cursor:
        subject_name = row[0]
        answer_keys = row[1]
    conn.close()
    return subject_name, answer_keys


###################################################################


################################VIEW SCANTRON AT TEST ID###################################
@Solution.route('/api/tests/<test_id>', methods=["GET"])
def view_all_scantrons_at_testid(test_id):
    response = view_scantron_record_at_testid(test_id)
    return jsonify(response)


def view_scantron_record_at_testid(test_id):
    response = dict()
    conn = sqlite3.connect('scantron.db')
    try:
        cursor = conn.execute("SELECT TEST_ID, SUBJECT, ANSWER_KEY from ANSWER_KEY_DB where TEST_ID=?", (test_id,))
        for row in cursor:
            response["test_id"] = row[0]
            response["subject"] = row[1]
            response["answer_keys"] = retransform_key(row[2])

        if test_id:
            subject_id = response["test_id"]
            cursor = conn.execute("SELECT SCANTRON_ID,NAME,SUBJECT,ANSWER_KEY from SCANTRON_DB where SUBJECT_ID=?",
                                  (subject_id,))
            submissions_list = list()
            for row in cursor:
                item = dict()
                item["scantron_id"] = row[0]
                item["scantron_url"] = "http://localhost:5000/files/scantron-" + str(row[0]) + ".json"
                item["name"] = row[1]
                item["subject"] = row[2]
                scores = calculate_score(transform_key(response["answer_keys"]), row[3])
                if scores is not None:
                    item['score'] = scores['score']
                    item['result'] = scores['result']
                    submissions_list.append(item)
                else:
                    continue
            response["submissions"] = submissions_list
        conn.close()
        return response

    except sqlite3.Error as e:
        conn.close()
        return "Database Error %s" % e

    except Exception as e:
        conn.close()
        return "Error %s" % e


###################################################################

def calculate_score(user_key, answer_key):
    score = 0
    result = dict()
    record = dict()
    user_key = retransform_key(user_key)
    answer_key = retransform_key(answer_key)
    try:
        for key in answer_key:
            try:
                result[key] = {"actual": user_key[key], "expected": answer_key[key]}
                if answer_key[key] == user_key[key]:
                    score = score + 1
            except KeyError:
                result[key] = {"actual": "Key Error", "expected": answer_key[key]}
                continue
        record["score"] = score
        record["result"] = result
        return record
    except Exception as e:
        return None


if __name__ == '__main__':
    create_databases()
    Solution.config['JSON_SORT_KEYS'] = False
    Solution.run(debug=True)

#   pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract'
#   print(pytesseract.image_to_string('sample1.jpg'))
#   binary_scantron = request.get_data()
#   get image of scantron and run the ocr library to extract the data , store in database
#   conn.execute("UPDATE COMPANY set Column_Name = Value where ID = 1")
#   conn.commit()
#   print("Total number of rows updated :", conn.total_changes)
#   conn.execute("DELETE from Column_Name where ID = 2;")
#   conn.commit()
#   print("Total number of rows deleted :", conn.total_changes)
#   print("Records created successfully")
#   conn.close()
