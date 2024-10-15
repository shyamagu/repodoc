package jp.test.front;

import jp.test.back.BackService;

public class FrontService {
    private final BackService backService;

    public FrontService(BackService backService) {
        this.backService = backService;
    }

    public void execute() {
        System.out.println("FrontService: Calling back service...");
        backService.performAction();
    }
}