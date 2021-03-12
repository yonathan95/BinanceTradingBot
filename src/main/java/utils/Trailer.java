package utils;

import com.binance.client.model.enums.PositionSide;

import java.math.BigDecimal;

public class Trailer {

    private BigDecimal absoluteMaxPrice;

    private BigDecimal exitPrice;

    private PositionSide side;

    Double trailingPercentage;

    public Trailer(BigDecimal currentPrice, Double trailingPercentage, PositionSide side){
        absoluteMaxPrice = currentPrice;
        this.side = side;
        this.trailingPercentage = trailingPercentage;
        if(side == PositionSide.LONG){
            exitPrice = calculateLongTrailingExitPrices(absoluteMaxPrice, trailingPercentage);
        }
        else{
            exitPrice = calculateShortTrailingExitPrices(absoluteMaxPrice, trailingPercentage);
        }
    }

    public void updateTrailer(BigDecimal currentPrice){
        if(side == PositionSide.LONG) {
            if (currentPrice.compareTo(absoluteMaxPrice) > 0) {
                absoluteMaxPrice = currentPrice;
                exitPrice = calculateLongTrailingExitPrices(absoluteMaxPrice, trailingPercentage);
            }
        }
        else{
            if (currentPrice.compareTo(absoluteMaxPrice) < 0 ) {
                absoluteMaxPrice = currentPrice;
                exitPrice = calculateShortTrailingExitPrices(absoluteMaxPrice, trailingPercentage);
            }
        }
    }

    public boolean needToSell(BigDecimal currentPrice){
        if (side == PositionSide.LONG) return currentPrice.compareTo(exitPrice) <= 0;
        else return currentPrice.compareTo(exitPrice) >= 0;
    }

    private BigDecimal calculateShortTrailingExitPrices(BigDecimal highestPrice, Double trailingPercentage) {
        return highestPrice.add((highestPrice.multiply(BigDecimal.valueOf(trailingPercentage)).multiply(BigDecimal.valueOf(1.0/100))));
    }

    private BigDecimal calculateLongTrailingExitPrices(BigDecimal highestPrice, Double trailingPercentage) {
            return highestPrice.subtract((highestPrice.multiply(BigDecimal.valueOf(trailingPercentage)).multiply(BigDecimal.valueOf(1.0/100))));
    }

    public BigDecimal getAbsoluteMaxPrice() {
        return absoluteMaxPrice;
    }

    public void setAbsoluteMaxPrice(BigDecimal absoluteMaxPrice) {
        this.absoluteMaxPrice = absoluteMaxPrice;
    }

    public BigDecimal getExitPrice() {
        return exitPrice;
    }

    public void setExitPrice(BigDecimal exitPrice) {
        this.exitPrice = exitPrice;
    }

    public PositionSide getSide() {
        return side;
    }

    public void setSide(PositionSide side) {
        this.side = side;
    }

    public Double getTrailingPercentage() {
        return trailingPercentage;
    }

    public void setTrailingPercentage(Double trailingPercentage) {
        this.trailingPercentage = trailingPercentage;
    }
}
