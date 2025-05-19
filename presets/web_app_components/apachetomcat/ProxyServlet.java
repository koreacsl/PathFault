import javax.servlet.*;
import javax.servlet.http.*;
import java.io.*;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.*;

public class ProxyServlet extends HttpServlet {
    private Map<String, Integer> portMap;
    private int tmpserverPort; // tmpserver 포트 저장

    @Override
    public void init() throws ServletException {
        String portMapPath = System.getenv("PORT_MAP_PATH");
        if (portMapPath == null || portMapPath.isEmpty()) {
            portMapPath = "/app/port_map.json"; // 기본 포트 매핑 파일 위치
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

                        // tmpserver 포트 저장 (항상 존재한다고 가정)
                        if (service.equals("tmpserver")) {
                            tmpserverPort = port;
                        }
                    }
                }
            }
        } catch (IOException e) {
            System.err.println("Failed to load port_map.json: " + e.getMessage());
        }

        // tmpserver가 정의되지 않았을 경우 기본 포트 8000 사용
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

        String service = segments[1]; // 첫 번째 경로 세그먼트 (서비스 이름)
        Integer port = portMap.get(service);

        // 매칭되지 않은 경우 전체 경로를 tmpserver로 전달해야 함
        if (port == null) {
            System.out.println("⚠️ Service not found: " + service + " → Redirecting to tmpserver");
            port = tmpserverPort;
            service = "tmpserver"; // tmpserver로 기본 설정

            // 기존 remainingPath가 아닌, 매칭이 실패한 서비스부터 전체 경로를 tmpserver로 전달
            StringBuilder newPath = new StringBuilder();
            for (int i = 1; i < segments.length; i++) { // 기존 service 포함
                newPath.append("/").append(segments[i]);
            }
            path = newPath.toString();
        } else {
            // 유효한 서비스인 경우 → service segment 제거
            StringBuilder newPath = new StringBuilder();
            for (int i = 2; i < segments.length; i++) {
                newPath.append("/").append(segments[i]);
            }
            path = newPath.length() > 0 ? newPath.toString() : "/";
        }

        // 최종 URL 구성 (쿼리 스트링 포함)
        String queryString = request.getQueryString();
        String targetUrl = "http://" + service + ":" + port + path;
        if (queryString != null) {
            targetUrl += "?" + queryString;
        }

        System.out.println("🔄 Forwarding request to: " + targetUrl);

        // 요청 바디를 미리 읽어 저장
        ByteArrayOutputStream bodyStream = new ByteArrayOutputStream();
        try (InputStream requestInputStream = request.getInputStream()) {
            byte[] buffer = new byte[8192];
            int bytesRead;
            while ((bytesRead = requestInputStream.read(buffer)) != -1) {
                bodyStream.write(buffer, 0, bytesRead);
            }
        }
        byte[] requestBody = bodyStream.toByteArray();

        // 요청 전달
        HttpURLConnection connection = (HttpURLConnection) new URL(targetUrl).openConnection();

        // **원본 요청의 HTTP 메소드를 강제 변경하지 않고 그대로 사용**
        connection.setRequestMethod(request.getMethod());
        connection.setInstanceFollowRedirects(false);
        connection.setDoInput(true);

        // Body가 있는 요청(GET 포함)에서도 `setDoOutput(true)` 유지
        if (requestBody.length > 0) {
            connection.setDoOutput(true);
        }

        // 요청 헤더 복사
        Enumeration<String> headerNames = request.getHeaderNames();
        while (headerNames.hasMoreElements()) {
            String headerName = headerNames.nextElement();
            if (!headerName.equalsIgnoreCase("transfer-encoding")) { // 청크 제거
                connection.setRequestProperty(headerName, request.getHeader(headerName));
            }
        }

        // 요청 바디 전송
        if (requestBody.length > 0) {
            try (OutputStream outputStream = connection.getOutputStream()) {
                outputStream.write(requestBody);
                outputStream.flush();
            }
        }

        // 응답 처리
        int responseCode = connection.getResponseCode();
        response.setStatus(responseCode);
        System.out.println("✅ Response Code from Target: " + responseCode);

        // 응답 헤더 복사
        connection.getHeaderFields().forEach((key, values) -> {
            if (key != null) {
                values.forEach(value -> response.addHeader(key, value));
            }
        });

        // 응답 바디 복사
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
            connection.disconnect(); // 연결 명확히 종료
        }
    }
}