import os
import glob
import re
import configparser

def decompile(ls, apk_name):
    if apk_name in ls and os.path.isdir(apk_name):
        print("El directorio de " + apk_name + " ya existe. No es necesario decompilar.")
    else:
        print("Decompilando " + apk_name + "... Este proceso puede tardar varios minutos.")
        os.system('jadx ' + apk_name + '.apk')
    if apk_or_folder_path.endswith('.apk'):
        dir_path = os.path.dirname(apk_or_folder_path) + '/' + apk_name
    else:
        dir_path = apk_or_folder_path + '/' + apk_name
    files = glob.glob(dir_path + '/**', recursive = True)
    return files

def search_for_pinning(files):
    resource_name = ""
    appName = ""

    with open(results, 'a') as resultFile:
        for file in files:
            try:
                with open(file, 'r') as f:
                    contents = f.read()
                    if 'AndroidManifest.xml' in file:
                        matchName = re.search(r'<application[^>]*\s+android:label="([^"]+)"[^>]*>', contents)
                        if matchName:
                            appName = matchName.group(1)
                            matchLabel = re.match(r'^@string/([a-zA-Z0-9_]+)$', appName)
                            if matchLabel:
                                resource_name = matchLabel.group(1)
            except:
                pass
        
        if resource_name:
            for file in files:
                try:
                    with open(file, 'r') as f:
                        contents = f.read()
                        if re.search(r'^.*?/res/values/strings\.xml$', file):
                            matchRegEx = rf'<string name="{resource_name}">([^<]+)</string>'
                            matchName = re.search(matchRegEx, contents)
                            if matchName:
                                appName = matchName.group(1)
                except:
                    pass
        
        #Metodo 1: TrustManager
        
        certPattern = r"res/raw/[^/]+\.(?:pem|cer|crt|key|der|pfx|p12|p7b|p7c)"
        keystorePattern = [ 
            r"(?i)KeyStore\.getInstance\(.*\)",
            r"(?i)KeyStore\.load\(.*\)"
        ]
        trustManagerPattern = [ 
            r"(?i)TrustManagerFactory\.getInstance\(.*\)",
            r"(?i)trustManagerFactory\.init\(.*\)"
        ]
        sslContextPattern = [ 
            r"(?i)SSLContext\.getInstance\(.*\)",
            r"(?i)SSLContext\.init\(.*\)"
        ]
        urlConnPattern = [ 
            r"(?i)URL\(\".+\"\)\.openConnection\(\)",
            r"(?i)\.setSSLSocketFactory\(sslcontext\.getsocketfactory\(\)\)"
        ]

        urlListPattern = r'URL\("([^"]+)"\)\.openConnection' 

        print("\n------------------------------------")
        print("Verificando metodo 1: TrustManager")
        global counter
        counter+=1
        resultFile.write("\n------------------------------------")
        resultFile.write(f"\n\n\nApk {counter}: Resultados de " + apk_name + "\n")
        print(f"Apk {counter}: Resultados de " + apk_name)
        if appName:
            resultFile.write(f"\nNombre de la aplicación: {appName}\n")
            print(f"Nombre de la aplicación: {appName}")
        resultFile.write("------------------------------------")
        resultFile.write("\nMetodo 1: TrustManager")

        keystore = False
        trustmanager = False
        sslcontext = False
        url = False
        certlist = []
        urlList = []
        trustManagerPinning = False

        for file in files:
            try:
                with open(file, 'r') as f:
                    contents = f.read()
                    if re.search(certPattern, file):
                        cert = file[file.rfind("/")+1:] 
                        certlist.append(cert)
                    keystore = False
                    if all(re.search(pattern, contents) for pattern in keystorePattern):
                        keystore = True
                    trustmanager = False
                    if all(re.search(pattern, contents) for pattern in trustManagerPattern):
                        trustmanager = True
                    sslcontext = False
                    if all(re.search(pattern, contents) for pattern in sslContextPattern):
                        sslcontext = True
                    url = False
                    if all(re.search(pattern, contents) for pattern in urlConnPattern):
                        url = True
                    if re.search(urlListPattern, contents):
                        currenturls = re.findall(urlListPattern, contents)
                        urlList.extend(currenturls)
                    if keystore and trustmanager and sslcontext and url:
                        trustManagerPinning = True
            except:
                pass

        if len(certlist) > 0:
            print("\nCertificados encontrados: ")
            resultFile.write("\nCertificados encontrados: ")
            for i in certlist:
                print("     " + i)
                resultFile.write("\n     " + i)
        else:
            print("No se ha encontrado ningun certificado")
            resultFile.write("\nNo se ha encontrado ningun certificado")

        urlList = list(set(urlList))
        if len(urlList) > 0:
            print("\nConexion con las siguientes URLs: ")
            resultFile.write("\nConexion con las siguientes URLs: ")
            for url in urlList:
                print("     " + url)
                resultFile.write("\n     " + url)
        else:
            print("\nNinguna conexion con URLs")
            resultFile.write("\nNinguna conexion con URLs")

        if trustManagerPinning:
            print("\nPinning con TrustManager implementado correctamente")
            resultFile.write("\nPinning con TrustManager implementado correctamente")
        else:
            print("\nTrustManager No implementado")
            resultFile.write("\nTrustManager No implementado")

        #Metodo 2: Okhttp Certificate Pinner

        toSearchCertPin = [
            r"CertificatePinner\.Builder\(\)\.add\(.+\)\.build\(\)",
            r"OkHttpClient\.Builder\(\)\.certificatePinner\(.+\)\.build\(\)"
        ]

        libraryfilter = [
            r"(?i)\/Okhttp\/",
            r"(?i)\/Okhttp3\/"
        ]

        certPinListPattern = r"CertificatePinner\.Builder\(\)((?:\.add\(([^)]+)\))*)"

        print("\n------------------------------------")
        print("Verificando metodo 2: OkHttp")
        resultFile.write("\n------------------------------------")
        resultFile.write("\nMetodo 2: OkHttp")

        okhttp = False
        certPinList = []
        okhttpPinning = False
        okhttpPinningFiltered = False

        for file in files:
            try:
                with open(file, 'r') as f:
                    contents = f.read()
                    okhttp = False
                    if all(re.search(pattern, contents) for pattern in toSearchCertPin):
                        okhttp = True
                        filtered = False
                        for pattern in libraryfilter:
                            if re.search(pattern, file):
                                filtered = True
                                okhttpPinningFiltered = True
                        else:
                            okhttpPinning = True
                            certPinList = re.findall(certPinListPattern, contents)
            except:
                pass

        if okhttpPinning:
            print("\nPinning mediante certificatePinner de okhttp implementado correctamente")
            resultFile.write("\nPinning mediante certificatePinner de okhttp implementado correctamente")
            certBuilderList = []
            
            for builder in certPinList:
                certBuilder = re.findall(r"\.add\(([^)]+)\)", builder[0])
                certBuilderList.extend(certBuilder)

            if len(certBuilderList) > 0:
                print("\nCertPin builders encontrados: ")
                resultFile.write("\nCertPin builders encontrados: ")
                for i  in certBuilderList:
                    print(i)
                    resultFile.write("\n" + i)
            
        else:
            if okhttpPinningFiltered:
                print("\nPinning de okhttp presente en libreria, pero no implementado")
                resultFile.write("\nPinning de okhttp presente en libreria, pero no implementado")
            else:
                print("\nOkhtpp certificatePinner: Sin implementar")
                resultFile.write("\nOkhtpp certificatePinner: Sin implementar")

        #Metodo 3: Network Security Config

        toSearchNSC = [
            r"\<domain\sincludeSubdomains\=\".+\"\>.+",
            r"\<pin\sdigest\=\".+\"\>.+"
        ]

        searchSHAURL = r'\<domain\sincludeSubdomains\="[^"]+">([^<]+)</domain>'
        searchSHAType = r'<pin digest="([^"]+)">[^<]+</pin>'
        searchSHA = r'<pin digest="[^"]+">([^<]+)</pin>'

        print("\n-------------------------------------------------")
        print("Verificando metodo 3: Network Security Config")
        resultFile.write("\n-------------------------------------------------")
        resultFile.write("\nMetodo 3: Network Security Config")

        nsc = False
        manifestbind = False
        sha = False
        shaList = []
        shaURLList = []
        shaTypeList = []

        for file in files:
            try:
                with open(file, 'r') as f:
                    contents = f.read()
                    if 'res/xml/network_security_config.xml' in file:
                        nsc = True
                        sha = False
                        if all(re.search(pattern, contents) for pattern in toSearchNSC):
                            sha = True
                        shaURLList = re.findall(searchSHAURL, contents)
                        shaTypeList = re.findall(searchSHAType, contents)
                        shaList = re.findall(searchSHA, contents)

                    if 'AndroidManifest.xml' in file:
                        if 'android:networkSecurityConfig="@xml/network_security_config"' in contents:
                            manifestbind = True            
            except:
                pass

        if nsc and sha and manifestbind:
            print("\nPinning mediante Network Security Configuration implementado correctamente")
            resultFile.write("\nPinning mediante Network Security Configuration implementado correctamente")
        else:
            print("\nPinning mediante Network Security Configuration: No implementado")
            resultFile.write("\nPinning mediante Network Security Configuration: No implementado")

        if nsc:
            print("\n     -Archivo networkSecurityConfig.xml presente en la aplicacion")
            resultFile.write("\n     -Archivo networkSecurityConfig.xml presente en la aplicacion")
            
            if manifestbind:
                print("     -Archivo emparejado con AndroidManifest.xml")
                resultFile.write("\n     -Archivo emparejado con AndroidManifest.xml")
            else:
                print("     -Archivo sin emparejar con AndroidManifest.xml")
                resultFile.write("\n     -Archivo sin emparejar con AndroidManifest.xml")
            
            if len(shaURLList) > 0:
                print("\nConexion con las siguientes URLs en NSC:")
                resultFile.write("\nConexion con las siguientes URLs en NSC:")
                for i in shaURLList:
                    print("     " + i)
                    resultFile.write("\n     " + i)
            else:
                print("Ninguna conexion con URLs en NSC")
                resultFile.write("\nNinguna conexion con URLs en NSC")
            
            if len(shaList) > 0:
                print("\nSHA encontrados en NSC: ")
                resultFile.write("\nSHA encontrados en NSC: ")
                for i, k in zip(shaTypeList, shaList):
                    print("     " + i + ": " + k)
                    resultFile.write("\n     " + i + ": " + k)
            else:
                print("\nNingun SHA encontrado en NSC")
                resultFile.write("\nNingun SHA encontrado en NSC")
        else:
            print("Archivo networkSecurityConfig.xml no encontrado")
            resultFile.write("\nArchivo networkSecurityConfig.xml no encontrado")

counter = 0
config = configparser.ConfigParser()
current_directory = os.path.dirname(os.path.abspath(__file__))

os.chdir(current_directory)
config.read('config.ini')

apk_or_folder_path = config['general']['APK']
results = config['general']['RESULTS']

if os.path.isfile(apk_or_folder_path) and apk_or_folder_path.endswith(".apk"):
    os.chdir(os.path.dirname(apk_or_folder_path))
    ls = os.listdir('.')
    apk_name = os.path.splitext(os.path.basename(apk_or_folder_path))[0]
    files = decompile(ls, apk_name)
    search_for_pinning(files)
elif os.path.isdir(apk_or_folder_path):
    os.chdir(apk_or_folder_path)
    ls = os.listdir('.')
    for filename in os.listdir(apk_or_folder_path):
        if filename.endswith('.apk'):
            apk_name = os.path.splitext(filename)[0]
            files = decompile(ls, apk_name)
            search_for_pinning(files)
else:
    print('Error: No se ha encontrado ningun directorio o APK.')