import vk_api
import requests
import os
import time
import re
import getpass

def vk_auth_api(login, password):
    """Access to vk.com api over vk_api lib"""
    vk_session = vk_api.VkApi(login, password)
    vk_session.auth()
    return vk_session.get_api()

def get_urls_photos(owner_id, album_id, vk_api):
    """Get list urls album photos"""
    urls_list_for_downloads=[]

    photos = vk_api.photos.get(owner_id=owner_id, album_id=album_id)

    for m_item in photos['items']:
        type_quality_photo=0
        #Array with api type quality photo("w"- high quality)
        types_quality_photo={'o': -1, 'p': -1, 'q': -1, 'r': -1, 's': 0, 'm': 1, 'x': 2, 'y': 3, 'z': 4, 'w': 5}
        #Find url with high quality
        url_max_quality=None
        for urls in m_item['sizes']:
            if type_quality_photo<types_quality_photo[urls['type']]:
                url_max_quality=urls['url']
                type_quality_photo=types_quality_photo[urls['type']]
        urls_list_for_downloads.append(url_max_quality)
    return urls_list_for_downloads

def create_dirs(saved_path, album_name):
    """Create directory with name album"""
    try:
        if not os.path.exists(saved_path):
            os.mkdir(saved_path)
        photo_folder = '{0}/{1}'.format(saved_path, album_name)
        if not os.path.exists(photo_folder):
            os.mkdir(photo_folder)
        return True
    except:
        return False

def download_image(url, saved_path, album_name, name_photo):
    """Download Photo in local directory"""
    response = requests.get(url, stream=True)
    local_file_name='{0}/{1}/{2}'.format(saved_path, album_name, name_photo)
    if not response.ok:
        print('bad response:', response)
        return 0
    try:
        with open(local_file_name, 'wb') as file:
            for chunk in response.iter_content(1024):
                file.write(chunk)
        return 1
    except IOError:
        print("Error save to {0}!".format(local_file_name))
        return 2

def start_downloading(urls_list_for_downloads, saved_path, album_name, photos_count):
    """Run function 'download_image' for items in list urls"""
    count = 0
    value_return=""

    for d_url in urls_list_for_downloads:
        name_photo = (d_url.split('?'))[0].split('/')[-1]
        status_download=download_image(d_url, saved_path, album_name, name_photo)
        if status_download==1:
            count += 1
            print("{0}/{1} Download {2}/{3}/{4}".format(count, photos_count, saved_path, album_name, name_photo))
        elif status_download==0:
            #If error download photo: 5 attempt with pause 5 seconds
            count_atempt=0
            while status_download==0:
                print("Error downloading!")
                print("Trying to download again after 5 seconds...")
                time.sleep(5)
                status_download=download_image(d_url, saved_path, album_name, name_photo)
                count_atempt+=1
                if count_atempt>5:
                    print("Error! Photo {1} from {0} not downloading!!! Try later...".format(album_name, name_photo))
                    value_return=album_name
                    break
        else:
            break
    return value_return

def _main(vk_api):
    """Main function download albums"""
    print("Enter album url or empty for download all albums:")
    url = input()

    saved_path='vk_photo'
    #If not input url - download all albums
    if url=="" or url==None or url=="empty":
        api_requests = vk_api.photos.getAlbums()#['items'][0]['title']
    else:
        album_id = url.split('/')[-1].split('_')[1]
        owner_id = url.split('/')[-1].split('_')[0].replace('album', '')
        api_requests = vk_api.photos.getAlbums(owner_id=owner_id, album_ids=album_id)

    albums_count=int(api_requests['count'])
    if albums_count==0:
        print("Album not found!")
    else:
        print("Found albums: {0}".format(albums_count))

    count_album_download=0
    errors_download=[]
    for album in api_requests['items']:
        print("Album downloading: ",album['title'])

        urls_list_for_downloads=get_urls_photos(album['owner_id'], album['id'], vk_api)

        #Delete spec simbols from name album
        name_album=re.sub("[$|@|&|.|!|#|%|*|;|'|<|>|/|\"|:|?|^|(|)|+|\|]", "", album['title'])
        name_album = re.sub("[ ]", "_", name_album)

        if create_dirs(saved_path, name_album):
            errors_down=start_downloading(urls_list_for_downloads, saved_path, name_album, album['size'])
            if errors_down!="":
                errors_download.append(errors_down)
            else:
                count_album_download +=1
        print("Download {0}/{1} albums".format(count_album_download, albums_count))

    for errs in errors_download:
        print("Errors download from {0} . Try latter...".format(errs))

def menu():
    auth = False

    while True:
        menu = """
        ________________________________________________

        VK_ALBUMS_DOWNLOADER 1.0
        https://github.com/Virtblch/VK_ALBUMS_DOWNLOADER
        ________________________________________________
        Enter:
        1 for downloading albums
        2 for exit
        """
        print(menu)
        in_menu = input()

        if in_menu == "1":
            if auth == False:

                print("Enter login:")
                login = input()
                print("Enter password:")
                password = getpass.getpass('Password:')

                try:
                    vk_api = vk_auth_api(login, password)
                    auth = True
                    _main(vk_api)
                except Exception as e:
                    print('Could not auth to vk.com')
                    print(e)
            else:
                _main(vk_api)

        elif in_menu == "2":
            break
        else:
            continue

if __name__ == '__main__':
    menu()
