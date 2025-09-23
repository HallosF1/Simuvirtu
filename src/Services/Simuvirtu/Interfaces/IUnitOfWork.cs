using Microsoft.EntityFrameworkCore.Storage;

namespace Simuvirtu.Interfaces
{
    public interface IUnitOfWork: IAsyncDisposable
    {
        Task<int> SaveChangesAsync(CancellationToken ct = default);
        Task<IDbContextTransaction> BeginTransactionAsync(CancellationToken ct = default);
        Task CommitAsync(IDbContextTransaction tx, CancellationToken ct = default);
        Task RollbackAsync(IDbContextTransaction tx);
    }
}
