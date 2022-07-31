# [shadowmoose](https://github.com/shadowmoose)'s [RedditDownloader](https://github.com/shadowmoose/RedditDownloader) Metadata to [Stash](https://stashapp.cc/) ([GitHub.com](https://github.com/stashapp/stash)) Database Python Script

## Idea from [OFMetadataToStash](https://github.com/ALonelyJuicebox/OFMetadataToStash) PowerShell script by [ALonelyJuicebox](https://github.com/ALonelyJuicebox)

## How script work
1. Read databases path from config file or from arguments
2. Get Reddit Studio ID from StashDB and if fail then create it
3. Read madia path from RedditDownloader Metadata DB
4. Try find this filepath in StashDB and if it success update its details, title, create date...
5. Link media to coresponding Performer and Studio

## Current state
* Filepath for media need to be same in both databases

## TODO
* Make Task plugin for Stash to make possible run this script from "Plugin Tasks"
  * Maybe find a way to create hook to run this script after scan in Stash

## Run in docker
```bash
docker image build --tag rdtostash:git .
docker run -it --rm --name rdtostash \
	-v ~/reddit/RDMetadataToStash.ini:/usr/src/app/RDMetadataToStash.ini \
	-v ~/reddit/manifest.sqlite:/usr/src/app/manifest.sqlite \
	-v ~/stash/stash-go.sqlite:/usr/src/app/stash-go.sqlite \
	rdtostash:git
```