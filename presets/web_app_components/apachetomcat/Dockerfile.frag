FROM tomcat:9.0.40-jdk15-openjdk

WORKDIR /usr/local/tomcat/

RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    apt-transport-https

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