jp.hogehoge.front;

public class Test {
    public static void main(String[] args) {
        FrontService frontService = new FrontService(new BackServiceImpl());
        frontService.execute();
    }
}