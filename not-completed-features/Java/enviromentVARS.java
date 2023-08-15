import java.io.FileWriter;
import java.io.IOException;

public class CreateSecretsFile {
    public static void main(String[] args) {
        String firebaseApiKey = "YOUR_FIREBASE_API_KEY";
        String firebaseSecret = "YOUR_FIREBASE_SECRET";

        String content = "FIREBASE_API_KEY=" + firebaseApiKey + "\nFIREBASE_SECRET=" + firebaseSecret;

        try {
            FileWriter writer = new FileWriter("secrets.env");
            writer.write(content);
            writer.close();
        } catch (IOException e) {
            e.printStackTrace();
        }
    }
}
