import os, getpass
from irods.session import iRODSSession

def getFilesonDE(base_path="/iplant/home/bhickson/2015/Data"):
	try:
		pw = getpass.getpass()
		session = iRODSSession(host='data.cyverse.org', zone="iplant", port=1247, user='bhickson', password=pw)

		data_col = session.collections.get(base_path)
	except:
		print("Unable to make connection to discover env. Continuing...")
		return None, {}

	global ifiles
	ifiles = {}
	
	def getFilesandDirs(dir):
		#print(dir.name)
		files_list = dir.data_objects
		dirs_list = dir.subcollections
		for file in files_list:
			file_name = file.name
			ifiles[file.name] = file.path
		for sub_dir in dirs_list:
        		#print(sub_dir.name)
			getFilesandDirs(sub_dir)

	getFilesandDirs(data_col)
	print("\t{} files found on Cyverse Discovery Environment in directory {}".format(len(ifiles),base_path))

	return session, ifiles


irods_sess, irods_files = getFilesonDE("/iplant/home/bhickson/2015/Data/NAIP")
print("NUM IRODS FILES: ", len(irods_files))

all_files = []
for root,dirs,files in os.walk("./"):
	all_files += [file for file in files if file.endswith(".tif")]
print("NUM ALL FILES: ", len(all_files))

count = 0
for file, path in irods_files.items():
	if file not in all_files and file.endswith(".tif"):
		count +=1
		print("\n{} - Downloading {}...\n".format(count, file))
		iget = "iget -Pv {} ./UTM12".format(path)
		os.system(iget)

print(count)
