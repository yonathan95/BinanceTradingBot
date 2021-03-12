package positions;

import java.math.BigDecimal;

public class SellingInstructions {
    private PositionHandler.ClosePositionTypes type;
    private BigDecimal sellingQtyPercentage;

    public SellingInstructions(PositionHandler.ClosePositionTypes type, BigDecimal sellingQtyPercentage) {
        this.type = type;
        this.sellingQtyPercentage = sellingQtyPercentage;
    }

    public PositionHandler.ClosePositionTypes getType() {
        return type;
    }

    public void setType(PositionHandler.ClosePositionTypes type) {
        this.type = type;
    }

    public BigDecimal getSellingQtyPercentage() {
        return sellingQtyPercentage;
    }

    public void setSellingQtyPercentage(BigDecimal sellingQtyPercentage) {
        this.sellingQtyPercentage = sellingQtyPercentage;
    }
}
