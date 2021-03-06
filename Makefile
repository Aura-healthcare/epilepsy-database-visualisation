up:
		docker-compose up

rm:
		docker rm -f $(docker ps -aq)
