import os

ATS_MAP_FILE = "/usr/local/etc/trafficserver/remap.config"  # ATS remap 설정 파일 경로
TMP_SERVER_PORT = os.getenv("TMP_SERVER_PORT", "8000")  # 기본 tmpserver 포트

def generate_ats_map():
    try:
        # ATS remap 설정 파일 생성
        with open(ATS_MAP_FILE, "w") as ats_file:
            # 모든 요청을 apachetomcat로 전달
            ats_file.write(f"map / http://apachetomcat:{8002}/\n")

        print(f"ATS remap file generated at {ATS_MAP_FILE}, all requests forwarded to apachetomcat:{8002}")
    except Exception as e:
        print(f"Error generating ATS remap file: {e}")

if __name__ == "__main__":
    generate_ats_map()