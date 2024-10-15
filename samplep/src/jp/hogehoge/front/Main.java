package jp.test.front;

import jp.test.back.BackService;
import jp.test.back.BackServiceImpl;

public class Main {
    public static void main(String[] args) {
        FrontService frontService = new FrontService(new BackServiceImpl());
        frontService.execute();
    }
}