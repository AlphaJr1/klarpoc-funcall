package domain

type DailySummary struct {
	Revenue        float64 `json:"revenue"`
	Transactions   int     `json:"transactions"`
	NewCustomers   int     `json:"new_customers"`
	TotalItemsSold float64 `json:"total_items_sold"`
}

type ProductMetric struct {
	Name     string `json:"name"`
	Quantity int    `json:"quantity"`
}

type EmployeePerformance struct {
	EmployeeName string  `json:"employee_name"`
	Sales        float64 `json:"sales"`
	Transactions int     `json:"transactions"`
}

type StoreInfo struct {
	ID          string  `json:"id"`
	Name        string  `json:"name"`
	Address     string  `json:"address"`
	City        string  `json:"city"`
	State       string  `json:"state"`
	PostalCode  string  `json:"postal_code"`
	Country     string  `json:"country"`
	PhoneNumber string  `json:"phone_number"`
	Description string  `json:"description"`
	CreatedAt   string  `json:"created_at"`
	UpdatedAt   string  `json:"updated_at"`
	DeletedAt   *string `json:"deleted_at"`
}

type DateRangeMetrics struct {
	StartDate      string  `json:"start_date"`
	EndDate        string  `json:"end_date"`
	Revenue        float64 `json:"revenue"`
	Transactions   int     `json:"transactions"`
	TotalItemsSold float64 `json:"total_items_sold"`
}

type LoyverseItem struct {
	ID                string                `json:"id"`
	Handle            string                `json:"handle"`
	ItemName          string                `json:"item_name"`
	Description       string                `json:"description"`
	ReferenceID       string                `json:"reference_id"`
	CategoryID        *string               `json:"category_id"`
	TrackStock        bool                  `json:"track_stock"`
	SoldByWeight      bool                  `json:"sold_by_weight"`
	IsComposite       bool                  `json:"is_composite"`
	UseProduction     bool                  `json:"use_production"`
	Components        []LoyverseComponent   `json:"components"`
	PrimarySupplierID string                `json:"primary_supplier_id"`
	TaxIDs            []string              `json:"tax_ids"`
	ModifiersIDs      []string              `json:"modifiers_ids"`
	Form              string                `json:"form"`
	Color             string                `json:"color"`
	ImageURL          string                `json:"image_url"`
	Option1Name       string                `json:"option1_name"`
	Option2Name       string                `json:"option2_name"`
	Option3Name       *string               `json:"option3_name"`
	CreatedAt         string                `json:"created_at"`
	UpdatedAt         string                `json:"updated_at"`
	DeletedAt         *string               `json:"deleted_at"`
	Variants          []LoyverseItemVariant `json:"variants"`
}

type LoyverseComponent struct {
	VariantID string  `json:"variant_id"`
	Quantity  float64 `json:"quantity"`
}

type LoyverseItemVariant struct {
	VariantID          string                 `json:"variant_id"`
	ItemID             string                 `json:"item_id"`
	SKU                string                 `json:"sku"`
	ReferenceVariantID string                 `json:"reference_variant_id"`
	Option1Value       string                 `json:"option1_value"`
	Option2Value       string                 `json:"option2_value"`
	Option3Value       *string                `json:"option3_value"`
	Barcode            string                 `json:"barcode"`
	Cost               float64                `json:"cost"`
	PurchaseCost       float64                `json:"purchase_cost"`
	DefaultPricingType string                 `json:"default_pricing_type"`
	DefaultPrice       *float64               `json:"default_price"`
	Stores             []LoyverseVariantStore `json:"stores"`
	CreatedAt          string                 `json:"created_at"`
	UpdatedAt          string                 `json:"updated_at"`
	DeletedAt          *string                `json:"deleted_at"`
}

type LoyverseVariantStore struct {
	StoreID          string   `json:"store_id"`
	PricingType      string   `json:"pricing_type"`
	Price            float64  `json:"price"`
	AvailableForSale bool     `json:"available_for_sale"`
	OptimalStock     *float64 `json:"optimal_stock"`
	LowStock         *float64 `json:"low_stock"`
}

type LoyverseReceipt struct {
	ReceiptNumber  string             `json:"receipt_number"`
	Note           *string            `json:"note"`
	ReceiptType    string             `json:"receipt_type"`
	RefundFor      *string            `json:"refund_for"`
	Order          *string            `json:"order"`
	CreatedAt      string             `json:"created_at"`
	ReceiptDate    string             `json:"receipt_date"`
	UpdatedAt      string             `json:"updated_at"`
	CancelledAt    *string            `json:"cancelled_at"`
	Source         string             `json:"source"`
	TotalMoney     float64            `json:"total_money"`
	TotalTax       float64            `json:"total_tax"`
	PointsEarned   float64            `json:"points_earned"`
	PointsDeducted float64            `json:"points_deducted"`
	PointsBalance  float64            `json:"points_balance"`
	CustomerID     string             `json:"customer_id"`
	TotalDiscount  float64            `json:"total_discount"`
	EmployeeID     string             `json:"employee_id"`
	StoreID        string             `json:"store_id"`
	PosDeviceID    string             `json:"pos_device_id"`
	DiningOption   string             `json:"dining_option"`
	TotalDiscounts []LoyverseDiscount `json:"total_discounts"`
	TotalTaxes     []LoyverseTax      `json:"total_taxes"`
	Tip            float64            `json:"tip"`
	Surcharge      float64            `json:"surcharge"`
	LineItems      []LoyverseLineItem `json:"line_items"`
	Payments       []LoyversePayment  `json:"payments"`
}

type LoyverseDiscount struct {
	ID          string  `json:"id"`
	Type        string  `json:"type"`
	Name        string  `json:"name"`
	Percentage  float64 `json:"percentage"`
	MoneyAmount float64 `json:"money_amount"`
}

type LoyverseTax struct {
	ID          string  `json:"id"`
	Type        string  `json:"type"`
	Name        string  `json:"name"`
	Rate        float64 `json:"rate"`
	MoneyAmount float64 `json:"money_amount"`
}

type LoyverseLineItem struct {
	ID              string             `json:"id"`
	ItemID          string             `json:"item_id"`
	VariantID       string             `json:"variant_id"`
	ItemName        string             `json:"item_name"`
	VariantName     *string            `json:"variant_name"`
	SKU             string             `json:"sku"`
	Quantity        float64            `json:"quantity"`
	Price           float64            `json:"price"`
	GrossTotalMoney float64            `json:"gross_total_money"`
	TotalMoney      float64            `json:"total_money"`
	Cost            float64            `json:"cost"`
	CostTotal       float64            `json:"cost_total"`
	LineNote        string             `json:"line_note"`
	LineTaxes       []LoyverseTax      `json:"line_taxes"`
	TotalDiscount   float64            `json:"total_discount"`
	LineDiscounts   []LoyverseDiscount `json:"line_discounts"`
	LineModifiers   []LoyverseModifier `json:"line_modifiers"`
}

type LoyverseModifier struct {
	ID               string  `json:"id"`
	ModifierOptionID string  `json:"modifier_option_id"`
	Name             string  `json:"name"`
	Option           string  `json:"option"`
	Price            float64 `json:"price"`
	MoneyAmount      float64 `json:"money_amount"`
}

type LoyversePayment struct {
	PaymentTypeID  string                  `json:"payment_type_id"`
	Name           string                  `json:"name"`
	Type           string                  `json:"type"`
	MoneyAmount    float64                 `json:"money_amount"`
	PaidAt         string                  `json:"paid_at"`
	PaymentDetails *LoyversePaymentDetails `json:"payment_details"`
}

type LoyversePaymentDetails struct {
	AuthorizationCode string      `json:"authorization_code"`
	ReferenceID       interface{} `json:"reference_id"`
	EntryMethod       string      `json:"entry_method"`
	CardCompany       string      `json:"card_company"`
	CardNumber        string      `json:"card_number"`
}

type LoyverseEmployee struct {
	ID          string   `json:"id"`
	Name        string   `json:"name"`
	Email       string   `json:"email"`
	PhoneNumber string   `json:"phone_number"`
	Stores      []string `json:"stores"`
	IsOwner     bool     `json:"is_owner"`
	CreatedAt   string   `json:"created_at"`
	UpdatedAt   string   `json:"updated_at"`
	DeletedAt   *string  `json:"deleted_at"`
}

type LoyverseRepository interface {
	GetDailySummary(storeID string, date string) (*DailySummary, error)
	GetTopProducts(storeID string, date string, limit int) ([]ProductMetric, error)
	GetEmployeePerformance(storeID string, date string) ([]EmployeePerformance, error)
	GetStoreInfo(storeID string) (*StoreInfo, error)
	GetDateRangeMetrics(storeID string, start, end string) (*DateRangeMetrics, error)
	GetItem(itemID string) (*LoyverseItem, error)
	ListItems() ([]LoyverseItem, error)
	GetReceipt(receiptNumber string) (*LoyverseReceipt, error)
	ListReceipts() ([]LoyverseReceipt, error)
	GetEmployee(employeeID string) (*LoyverseEmployee, error)
	ListEmployees() ([]LoyverseEmployee, string, error)
}
