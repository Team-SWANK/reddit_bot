import configparser

def get_client_id():
    config = configparser.ConfigParser()
    config.read('imgur_auth.ini')

    client_id = config.get('imgur', 'client_id')

    return client_id

if __name__ == "__main__":
    get_client_id()