from vk_api import VkApi
import requests
import os
import time
import re
import getpass


class Albums:
    def __init__(self, url, vk_api):
        self.api_requests = None
        self.url = url
        self.vk_api = vk_api
        self.errors_download = []

    def get(self):
        """Get list albums from vk_api"""
        lst_albums = None
        try:
            # If not input url - download all user albums
            if self.url == "" or self.url is None or self.url == "empty":
                self.api_requests = self.vk_api.photos.getAlbums()
            else:
                album_id = self.url.split('/')[-1].split('_')[1]
                owner_id = self.url.split('/')[-1].split('_')[0].replace('album', '')
                self.api_requests = self.vk_api.photos.getAlbums(owner_id=owner_id, album_ids=album_id)
            lst_albums = self.api_requests
        except Exception as e:
            print("Error get albums list! ", e)
        return lst_albums

    def count(self):
        """Get albums count"""
        try:
            return int(self.api_requests['count'])
        except Exception as e:
            print("Error get count albums! ", e)
            return 0

    def get_urls_photos(self, owner_id, album_id):
        """Get list urls album photos"""
        urls_list_for_downloads = []
        # api vk get max 1000 photo.
        # Get 200 photo in cycle
        get_count_photo = 200
        offset_photo = 0
        try:
            photos = self.vk_api.photos.get(owner_id=owner_id, album_id=album_id, count=get_count_photo,
                                            offset=offset_photo)
            all_count_in_album = photos['count']

            # Array with api type quality photo("w"- high quality)
            types_quality_photo = {'o': -1, 'p': -1, 'q': -1, 'r': -1, 's': 0, 'm': 1, 'x': 2, 'y': 3, 'z': 4, 'w': 5}

            while offset_photo < all_count_in_album:
                for m_item in photos['items']:
                    type_quality_photo = 0
                    # Find url with high quality
                    url_max_quality = None
                    for urls in m_item['sizes']:
                        if type_quality_photo < types_quality_photo[urls['type']]:
                            url_max_quality = urls['url']
                            type_quality_photo = types_quality_photo[urls['type']]
                    urls_list_for_downloads.append(url_max_quality)
                offset_photo += get_count_photo
                photos = self.vk_api.photos.get(owner_id=owner_id, album_id=album_id, count=get_count_photo,
                                                offset=offset_photo)
        except Exception as e:
            print("Error parse list urls!", e)
        return urls_list_for_downloads

    @staticmethod
    def create_dir(saved_path, album_name):
        """Create directory with name album"""
        ok = True
        try:
            if not os.path.exists(saved_path):
                os.mkdir(saved_path)
            photo_folder = '{0}/{1}'.format(saved_path, album_name)
            if not os.path.exists(photo_folder):
                os.mkdir(photo_folder)
                if not os.path.exists(photo_folder):
                    ok = False
        except Exception as e:
            print('Error create album directory: ', e)
            ok = False
        return ok

    @staticmethod
    def __download_image(url, saved_path, album_name, name_photo):
        """Download Photo in local directory"""
        try:
            response = requests.get(url, stream=True)
        except Exception as e:
            print(e)
            return 0

        local_file_name = '{0}/{1}/{2}'.format(saved_path, album_name, name_photo)
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

    def save(self, urls_list_for_downloads, saved_path, album_name, album_id, owner_id, photos_count):
        """Run  '__download_image' for items in list urls"""
        count = 0
        value_return = ""

        for d_url in urls_list_for_downloads:
            name_photo = (d_url.split('?'))[0].split('/')[-1]
            status_download = self.__download_image(d_url, saved_path, album_name, name_photo)
            if status_download == 1:
                count += 1
                print("{0}/{1} Download in {2}/{3}/{4}".format(count, photos_count, saved_path, album_name, name_photo))
            elif status_download == 0:
                # If error download photo: 10 attempt with pause 5 seconds
                count_atempt = 0
                while status_download == 0:
                    print("Error downloading!")
                    print("Trying to download again after 5 seconds...")
                    time.sleep(5)
                    status_download = self.__download_image(d_url, saved_path, album_name, name_photo)
                    if status_download == 1:
                        count += 1
                        print("{0}/{1} Download {2}/{3}/{4}".format(count, photos_count, saved_path, album_name,
                                                                    name_photo))
                    count_atempt += 1
                    if count_atempt > 10:
                        print(
                            "Error! Photo {1} from {0} not downloading!!! Try later...".format(album_name, name_photo))
                        value_return = album_name + ' https://vk.com/album' + str(owner_id) + '_' + str(album_id)
                        break
            else:
                break
        if value_return != "":
            self.errors_download.append(value_return)
        return value_return

    def get_err_download(self):
        return self.errors_download


def vk_auth_api(login, password):
    """Access to vk.com api over vk_api lib"""
    vk_session = VkApi(login, password)
    vk_session.auth()
    return vk_session.get_api()


def download(vk_api):
    """Run prepare, download, save albums photo"""
    print("Enter album url (example: https://vk.com/album-33964908_150436522 ) or empty for download all your albums:")
    url = input()

    saved_path = 'vk_photo'

    print('Start download: ', time.ctime())

    albums = Albums(url, vk_api)
    lst_albums = albums.get()
    if lst_albums is not None:
        albums_count = albums.count()
        if albums_count == 0:
            print("Album not found!")
            return
        else:
            print("Found albums: {0}".format(albums_count))
    else:
        return

    count_album_download = 0
    errors_download = []

    for album in lst_albums['items']:
        print("Album downloading: ", album['title'])
        urls_list_for_downloads = albums.get_urls_photos(album['owner_id'], album['id'])
        if urls_list_for_downloads == {}:
            print("Error: urls list is empty!")
            break

        # Delete spec simbols from name album
        name_album = re.sub("[$|@|&|.|!|#|%|*|;|'|<|>|/|\"|:|?|^|(|)|+|\|]", "", album['title'])
        name_album = re.sub("[ ]", "_", name_album)

        # create_dirs(saved_path, name_album)
        if not albums.create_dir(saved_path, name_album):
            break

        errors_down = albums.save(urls_list_for_downloads, saved_path, name_album, album['id'], album['owner_id'],
                                  album['size'])

        if errors_down != "":
            errors_download.append(errors_down)
        else:
            count_album_download += 1

        print("Download {0}/{1} albums in {2}".format(count_album_download, albums_count, saved_path))

    for errs in albums.get_err_download():
        print("Errors download from {0} . Download this album again or try latter...".format(errs))


def menu():
    """Main menu"""
    auth = False

    while True:
        menus = """
 ___________________________________________

 VK_ALBUMS_DOWNLOADER 1.1
 https://github.com/Virtblch/DownloadPhotoVK
 ___________________________________________
 Enter:
    1 for downloading albums
    2 for exit
    
"""
        print(menus)
        in_menu = input()

        if in_menu == "1":
            if not auth:

                print("Enter login:")
                login = input()
                print("Enter password:")
                password = getpass.getpass('Password:')
                try:
                    vk_api = vk_auth_api(login, password)
                    auth = True
                except Exception as e:
                    print('Could not auth to vk.com', e)
                    continue
                download(vk_api)
            else:
                download(vk_api)
            print('Stop download: ', time.ctime())

        elif in_menu == "2":
            break
        else:
            continue


if __name__ == '__main__':
    menu()
