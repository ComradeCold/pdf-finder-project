import mysql.connector

config = {
    'user': 'appuser',
    'password': 'Ajiefw9340*',
    'host': '34.66.54.180',
    'database': 'pdf_finder'
}

def store_click(link_url):
    cnx = mysql.connector.connect(**config)
    cursor = cnx.cursor()

    # Check if link exists
    cursor.execute("SELECT id FROM pdf_clicks WHERE link_url = %s", (link_url,))
    exists = cursor.fetchone()

    if exists:
        print("Link already saved, not inserting again.")
    else:
        cursor.execute("INSERT INTO pdf_clicks (link_url) VALUES (%s)", (link_url,))
        cnx.commit()
        print("Stored new link:", link_url)

    cursor.close()
    cnx.close()


def print_clicks():
    cnx = mysql.connector.connect(**config)
    cursor = cnx.cursor()
    cursor.execute("SELECT id, link_url, click_time FROM pdf_clicks ORDER BY id DESC")

    print("+----+--------------------------------------+---------------------+")
    print("| id | link_url                            | click_time          |")
    print("+----+--------------------------------------+---------------------+")
    for row in cursor.fetchall():
        print("| {:<2} | {:<38} | {} |".format(row[0], row[1][:38], row[2]))
    print("+----+--------------------------------------+---------------------+")

    cursor.close()
    cnx.close()


if __name__ == "__main__":
    try:
        with open("test.txt") as f:
            link = f.readline().strip() # reads first line only
            if link:
                store_click(link)
    except:
        print("test.txt not found!")

    print_clicks()
