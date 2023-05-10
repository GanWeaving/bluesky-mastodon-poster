import os
import io
from mastodon import Mastodon
from PIL import Image
from getpass import getpass
from atproto import Client, models
from datetime import datetime
import curses
import curses.ascii
import sys

PROMPT_TEXT = "Warning: Text is too long. Please edit the text to 300 characters or less."
CHOICE_PROMPT = "Choose an option:\n(1) Post images\n(2) Post text\n(3) Exit\nYour choice: "

def resize_image(image_file, max_size_kb=976.56, max_iterations=4):
    img = Image.open(image_file)
    img_format = img.format

    for _ in range(max_iterations):
        img_data = io.BytesIO()
        img.save(img_data, format=img_format)
        img_data.seek(0)

        if len(img_data.getvalue()) / 1024 <= max_size_kb:
            return img_data.getvalue()

        img.thumbnail((img.width * 0.9, img.height * 0.9), Image.LANCZOS)

    return None

def get_multiline_input(prompt):
    print(prompt)
    lines = []
    for line in iter(input, 'END'):
        lines.append(line)
    return '\n'.join(lines)

def edit_text_window(stdscr, prompt, initial_text):
    curses.echo()
    stdscr.addstr(0, 0, prompt)
    stdscr.refresh()

    text = initial_text
    while True:
        stdscr.addstr(1, 0, f"Current text length: {len(text)} characters")
        stdscr.addstr(2, 0, "Edit the text below to 300 characters or less (Press ENTER to finish):")
        stdscr.addstr(3, 0, text)
        stdscr.refresh()

        ch = stdscr.getch()
        if ch == curses.ascii.CR:
            break
        elif ch in [curses.ascii.BS, 127] and text:
            text = text[:-1]
            stdscr.addstr(3, 0, " " * (len(text) + 1))
            stdscr.move(3, 0)
            stdscr.addstr(3, 0, text)
        else:
            text += chr(ch)

    return text

def edit_text(text):
    return curses.wrapper(edit_text_window, PROMPT_TEXT, text)

def post_images(client, mastodon):
    image_extensions = ('.jpg', '.jpeg', '.png')
    image_files = sorted([f for f in os.listdir('.') if f.lower().endswith(image_extensions)])[:4]
    
    if not image_files:
        print("No images found. Exiting.")
        return

    text = get_multiline_input("Enter the text for the post (end input with 'END'): ")
    while len(text) >     300:
        text = edit_text(text)

    images, mastodon_images = [], []

    for image_file in image_files:
        try:
            img_data = resize_image(image_file)
            if img_data is None:
                print(f"Failed to resize {image_file} within the limit. Skipping this image.")
                continue

            alt_text = input(f"Enter the alt text for {image_file}: ")

            upload = client.com.atproto.repo.upload_blob(img_data)
            images.append(models.AppBskyEmbedImages.Image(alt=alt_text, image=upload.blob))

            with open(image_file, 'rb') as f:
                media = mastodon.media_post(f.read(), mime_type='image/jpeg', description=alt_text)
            mastodon_images.append(media['id'])

        except Exception as e:
            print(f"An error occurred while processing {image_file}: {e}. Skipping this image.")
            continue

        finally:
            os.remove(image_file)

    if not images:
        print("No valid images were processed. Exiting.")
        return

    # Post to Mastodon
    mastodon.status_post(text, media_ids=mastodon_images)

    embed = models.AppBskyEmbedImages.Main(images=images)

    client.com.atproto.repo.create_record(
        models.ComAtprotoRepoCreateRecord.Data(
            repo=client.me.did,
            collection='app.bsky.feed.post',
            record=models.AppBskyFeedPost.Main(
                createdAt=datetime.now().isoformat(), text=text, embed=embed
            ),
        )
    )

    print("Images posted on Mastodon & Bluesky! What else do you want to do?")

def post_text(client, mastodon):
    text = get_multiline_input("Enter the text for the post (end input with 'END'): ")

    while len(text) > 300:
        text = edit_text(text)

    # Post to Bluesky
    client.send_post(text=text)

    # Post to Mastodon
    mastodon.status_post(text)

    print("Text posted! What else do you want to do?")

def exit_program(client, mastodon):
    sys.exit()

def main():
    client = Client()
    email =  'your_email' 
    password = 'your_password' 
    client.login(email, password)

    mastodon = Mastodon(
        client_id='your_id',
        client_secret='your_secret',
        access_token='your_token',
        api_base_url='your_url' 
    )

    actions = {'1': post_images, '2': post_text, '3': exit_program}

    while True:
        action = input(CHOICE_PROMPT)
        try:
            actions[action](client, mastodon)
        except KeyError:
            print("Invalid input. Please try again.")

if __name__ == '__main__':
    main()

