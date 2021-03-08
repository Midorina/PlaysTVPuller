import argparse
import pathlib

import exceptions
import models

parser = argparse.ArgumentParser(description='Download most of your Plays.TV videos from the web archive.')

parser.add_argument(
    'username',
    help='your Plays.TV username')
parser.add_argument(
    '--download_path',
    default='downloads',
    help='the directory where all videos will be placed in')
parser.add_argument(
    '--overwrite',
    default=False,
    action='store_true',
    help='overwrite/re-download if the video is already downloaded')

args = parser.parse_args()

# first check if the directory exists
pathlib.Path(args.download_path).mkdir(parents=True, exist_ok=True)

browser = models.ArchivedPlaysTVBrowser(user_name=args.username)

try:
    print("https://midorina.dev || Feel free to contact me if you have questions or issues ♥\n\n"
          "Launching the browser. Do not close it until we're done.\n"
          "Internet Archive's website is noticeably slow, so this may take a while...\n")

    try:
        browser.launch_the_browser()
    except exceptions.NotArchived:
        print("Looks like your profile is not archived at all... This is weird.\n"
              "This might be an issue from Internet Archive's API. "
              "If you think this is a mistake, try again in a few minutes.")
        exit()

    print(f"You seem to have {browser.total_video_count} videos on Plays.TV\n"
          f"{browser.author_video_count} of them are uploaded by you, and you're featured in {browser.featured_video_count} other videos.")

    print("\nNow we will scroll down until all videos are visible. Please wait...")
    browser.scroll_down_until_all_videos_are_visible()

    print(f"Done. Now processing each video...\n")
    for video in browser.get_all_visible_videos():
        print(f"Attempting to download the highest quality of video: {video.title}")
        try:
            video.attempt_to_download_highest_quality(directory=args.download_path, overwrite=args.overwrite)
        except (exceptions.NotArchived, exceptions.AlreadyDownloaded) as e:
            print(e)
        else:
            print(f"Done!")
        finally:
            print()
finally:
    browser.close()
