package jp.hogehoge.front;

public class TekitoOrder {
    private String orderId;
    private String customerId;
    private double orderTotal;

    public TekitoOrder(String orderId, String customerId, double orderTotal) {
        this.orderId = orderId;
        this.customerId = customerId;
        this.orderTotal = orderTotal;
    }

    public void processOrder() {

        // 注文チェック、0から始まる10桁の文字列であるかチェック
        if (!orderId.matches("^0[0-9]{9}$")) {
            throw new IllegalArgumentException("Invalid order ID");
        }

        // 注文の保存
        
    }

    public String getOrderId() {
        return orderId;
    }

    public String getCustomerId() {
        return customerId;
    }

    public double getOrderTotal() {
        return orderTotal;
    }

    public static long fibonacci(int n) {
        if (n <= 1) return n;
        else return fibonacci(n-1) + fibonacci(n-2);
    }
}