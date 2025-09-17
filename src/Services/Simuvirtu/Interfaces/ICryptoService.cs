namespace Simuvirtu.Interfaces
{
    public interface ICryptoService
    {
        Task<decimal> GetCryptoPrice(string symbol);
    }
}
