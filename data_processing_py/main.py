import dotenv
from sub_data import Subcribe

def main():
	app_client_id = dotenv.get_key(dotenv_path='.env', key_to_get='EMOTIV_APP_CLIENT_ID')
	app_client_secret = dotenv.get_key(dotenv_path='.env', key_to_get='EMOTIV_APP_CLIENT_SECRET')

	if not app_client_id or not app_client_secret:
		print("Please set EMOTIV_APP_CLIENT_ID and EMOTIV_APP_CLIENT_SECRET in .env file")
		return
	
	print("Starting subscription with client ID:", app_client_id)
	print("Starting subscription with secret.")

	s = Subcribe(app_client_id, app_client_secret)
	streams = ['dev', 'eq', 'pow', 'met']

	s.start(streams)

if __name__ == "__main__":
	main()