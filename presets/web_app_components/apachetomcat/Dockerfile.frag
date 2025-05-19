# Tomcat 9 기반 이미지 사용
FROM tomcat:9.0.40-jdk15-openjdk

# 작업 디렉토리 설정
WORKDIR /usr/local/tomcat/

# apt 소스 및 패키지 설치
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    apt-transport-https

# ProxyServlet.java 복사
COPY ProxyServlet.java /usr/local/tomcat/webapps/ROOT/WEB-INF/classes/

# Servlet 컴파일
RUN javac -cp "/usr/local/tomcat/lib/servlet-api.jar" \
    -d /usr/local/tomcat/webapps/ROOT/WEB-INF/classes/ \
    /usr/local/tomcat/webapps/ROOT/WEB-INF/classes/ProxyServlet.java

# web.xml 설정
RUN mkdir -p /usr/local/tomcat/webapps/ROOT/WEB-INF/ && \
    echo "<?xml version=\"1.0\" encoding=\"UTF-8\"?>" > /usr/local/tomcat/webapps/ROOT/WEB-INF/web.xml && \
    echo "<web-app xmlns=\"http://java.sun.com/xml/ns/javaee\" version=\"3.0\">" >> /usr/local/tomcat/webapps/ROOT/WEB-INF/web.xml && \
    echo "<servlet><servlet-name>ProxyServlet</servlet-name><servlet-class>ProxyServlet</servlet-class></servlet>" >> /usr/local/tomcat/webapps/ROOT/WEB-INF/web.xml && \
    echo "<servlet-mapping><servlet-name>ProxyServlet</servlet-name><url-pattern>/*</url-pattern></servlet-mapping>" >> /usr/local/tomcat/webapps/ROOT/WEB-INF/web.xml && \
    echo "</web-app>" >> /usr/local/tomcat/webapps/ROOT/WEB-INF/web.xml