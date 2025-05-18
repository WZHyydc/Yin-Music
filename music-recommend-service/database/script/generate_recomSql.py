import random
import datetime
import json

now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
insert_statements = []

for user_id in range(1, 51):
    song_ids = random.sample(range(1, 101), 10)
    json_list = json.dumps(song_ids)
    stmt = (
        "INSERT INTO user_recommendations "
        "(user_id, recommend_time, model_version, song_ids) "
        f"VALUES ({user_id}, '{now}', 'SASRec', '{json_list}');"
    )
    insert_statements.append(stmt)

# Display the generated SQL statements
for stmt in insert_statements:
    print(stmt)
