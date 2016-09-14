sudo umount -f /captured
cd /home/pi/meetingroom
sudo mount -t cifs -o gid=1000,uid=1000,username='ch.tseng',password='2laiuool@e020770E' //172.30.16.231/meetingroom$ /captured/
python3 main.py
