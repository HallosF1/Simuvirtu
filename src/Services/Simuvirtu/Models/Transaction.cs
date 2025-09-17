using System.ComponentModel.DataAnnotations.Schema;

namespace Simuvirtu.Models
{
    public class Transaction
    {
        public int Id { get; set; }
        [ForeignKey("Portfolio")]
        public int PortfolioId { get; set; }
        public Portfolio Portfolio { get; set; }
        public string Symbol { get; set; }
        public float Quantity { get; set; }
        public decimal Price { get; set; }
        public DateTime TimeStamp { get; set; } = DateTime.UtcNow;
    }
}
