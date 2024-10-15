package jp.test.back;

public class BackServiceImpl implements BackService {
    @Override
    public void performAction() {
        System.out.println("BackServiceImpl: Action performed!");
    }
}