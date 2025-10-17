FROM tomcat:9.0.40-jdk15-openjdk

WORKDIR /usr/local/tomcat/

RUN set -eux; \
    sed -i 's|deb.debian.org/debian|archive.debian.org/debian|g' /etc/apt/sources.list; \
    sed -i 's|security.debian.org/debian-security|archive.debian.org/debian-security|g' /etc/apt/sources.list; \
    sed -i '/buster-updates/d' /etc/apt/sources.list; \
    printf 'Acquire::Check-Valid-Until "false";\n' > /etc/apt/apt.conf.d/99no-check-valid-until; \
    apt-get -o Acquire::Check-Valid-Until=false update; \
    apt-get install -y --no-install-recommends \
        wget \
        gnupg \
        ca-certificates \
        apt-transport-https; \
    rm -rf /var/lib/apt/lists/*

COPY ProxyServlet.java /usr/local/tomcat/webapps/ROOT/WEB-INF/classes/

RUN javac -cp "/usr/local/tomcat/lib/servlet-api.jar" \
    -d /usr/local/tomcat/webapps/ROOT/WEB-INF/classes/ \
    /usr/local/tomcat/webapps/ROOT/WEB-INF/classes/ProxyServlet.java

RUN mkdir -p /usr/local/tomcat/webapps/ROOT/WEB-INF/ && \
    echo "<?xml version=\"1.0\" encoding=\"UTF-8\"?>" > /usr/local/tomcat/webapps/ROOT/WEB-INF/web.xml && \
    echo "<web-app xmlns=\"http://java.sun.com/xml/ns/javaee\" version=\"3.0\">" >> /usr/local/tomcat/webapps/ROOT/WEB-INF/web.xml && \
    echo "<servlet><servlet-name>ProxyServlet</servlet-name><servlet-class>ProxyServlet</servlet-class></servlet>" >> /usr/local/tomcat/webapps/ROOT/WEB-INF/web.xml && \
    echo "<servlet-mapping><servlet-name>ProxyServlet</servlet-name><url-pattern>/*</url-pattern></servlet-mapping>" >> /usr/local/tomcat/webapps/ROOT/WEB-INF/web.xml && \
    echo "</web-app>" >> /usr/local/tomcat/webapps/ROOT/WEB-INF/web.xml