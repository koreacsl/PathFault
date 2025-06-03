import javax.servlet.*;
import javax.servlet.http.*;
import java.io.*;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.*;

public class ProxyServlet extends HttpServlet {
    private Map<String, Integer> portMap;
    private int tmpserverPort;

    @Override
    public void init() throws ServletException {
        String portMapPath = System.getenv("PORT_MAP_PATH");
        if (portMapPath == null || portMapPath.isEmpty()) {
            portMapPath = "/app/port_map.json";
        }

        portMap = new HashMap<>();
        try (BufferedReader reader = new BufferedReader(new FileReader(portMapPath))) {
            StringBuilder jsonBuilder = new StringBuilder();
            String line;
            while ((line = reader.readLine()) != null) {
                jsonBuilder.append(line);
            }

            String jsonString = jsonBuilder.toString();
            if (!jsonString.isEmpty()) {
                jsonString = jsonString.replace("{", "").replace("}", "").replace("\"", "");
                String[] entries = jsonString.split(",");
                for (String entry : entries) {
                    String[] keyValue = entry.split(":");
                    if (keyValue.length == 2) {
                        String service = keyValue[0].trim();
                        int port = Integer.parseInt(keyValue[1].trim());
                        portMap.put(service, port);

                        if (service.equals("tmpserver")) {
                            tmpserverPort = port;
                        }
                    }
                }
            }
        } catch (IOException e) {
            System.err.println("Failed to load port_map.json: " + e.getMessage());
        }

        if (tmpserverPort == 0) {
            tmpserverPort = 8000;
        }

        System.out.println("🔧 Loaded port map: " + portMap);
        System.out.println("✅ tmpserverPort set to: " + tmpserverPort);
    }

    @Override
    protected void service(HttpServletRequest request, HttpServletResponse response) throws IOException {
        String path = request.getPathInfo();
        if (path == null || path.equals("/")) {
            response.setStatus(HttpServletResponse.SC_OK);
            response.getWriter().write("OK");
            return;
        }

        String[] segments = path.split("/");
        if (segments.length < 2) {
            response.setStatus(HttpServletResponse.SC_BAD_REQUEST);
            response.getWriter().write("Invalid request path");
            return;
        }

        String service = segments[1];
        Integer port = portMap.get(service);

        if (port == null) {
            System.out.println("⚠️ Service not found: " + service + " → Redirecting to tmpserver");
            port = tmpserverPort;
            service = "tmpserver";

            StringBuilder newPath = new StringBuilder();
            for (int i = 1; i < segments.length; i++) {
                newPath.append("/").append(segments[i]);
            }
            path = newPath.toString();
        } else {
            StringBuilder newPath = new StringBuilder();
            for (int i = 2; i < segments.length; i++) {
                newPath.append("/").append(segments[i]);
            }
            path = newPath.length() > 0 ? newPath.toString() : "/";
        }

        String queryString = request.getQueryString();
        String targetUrl = "http://" + service + ":" + port + path;
        if (queryString != null) {
            targetUrl += "?" + queryString;
        }

        System.out.println("🔄 Forwarding request to: " + targetUrl);

        ByteArrayOutputStream bodyStream = new ByteArrayOutputStream();
        try (InputStream requestInputStream = request.getInputStream()) {
            byte[] buffer = new byte[8192];
            int bytesRead;
            while ((bytesRead = requestInputStream.read(buffer)) != -1) {
                bodyStream.write(buffer, 0, bytesRead);
            }
        }
        byte[] requestBody = bodyStream.toByteArray();

        HttpURLConnection connection = (HttpURLConnection) new URL(targetUrl).openConnection();

        connection.setRequestMethod(request.getMethod());
        connection.setInstanceFollowRedirects(false);
        connection.setDoInput(true);

        if (requestBody.length > 0) {
            connection.setDoOutput(true);
        }

        Enumeration<String> headerNames = request.getHeaderNames();
        while (headerNames.hasMoreElements()) {
            String headerName = headerNames.nextElement();
            if (!headerName.equalsIgnoreCase("transfer-encoding")) {
                connection.setRequestProperty(headerName, request.getHeader(headerName));
            }
        }

        if (requestBody.length > 0) {
            try (OutputStream outputStream = connection.getOutputStream()) {
                outputStream.write(requestBody);
                outputStream.flush();
            }
        }

        int responseCode = connection.getResponseCode();
        response.setStatus(responseCode);
        System.out.println("✅ Response Code from Target: " + responseCode);

        connection.getHeaderFields().forEach((key, values) -> {
            if (key != null) {
                values.forEach(value -> response.addHeader(key, value));
            }
        });

        try (InputStream inputStream = connection.getInputStream();
             OutputStream outputStream = response.getOutputStream()) {
            byte[] buffer = new byte[8192];
            int bytesRead;
            while ((bytesRead = inputStream.read(buffer)) != -1) {
                outputStream.write(buffer, 0, bytesRead);
            }
        } catch (IOException e) {
            System.err.println("❌ Error copying response body: " + e.getMessage());
        } finally {
            connection.disconnect();
        }
    }
}