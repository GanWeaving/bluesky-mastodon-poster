from mastodon import Mastodon

# Define your application's info
app_name = 'postToMastodon'  # replace with your actual data
scopes = ['read', 'write', 'follow', 'push']  # permissions your app is requesting
mastodon_instance_url = 'your_url'  # replace with your actual data

# Register your application
client_id, client_secret = Mastodon.create_app(
    client_name=app_name,
    scopes=scopes,
    api_base_url=mastodon_instance_url
)

# Print the client key and secret
print('Client key:', client_id)
print('Client secret:', client_secret)

# Define the user's info
username = 'username'  # replace with your actual data
password = 'password.'  # replace with your actual data

# Create a Mastodon instance
mastodon = Mastodon(
    client_id=client_id,
    client_secret=client_secret,
    api_base_url=mastodon_instance_url
)

# Log in to the user's account
access_token = mastodon.log_in(
    username=username,
    password=password,
    scopes=scopes
)

# Print the access token
print('Access token:', access_token)
