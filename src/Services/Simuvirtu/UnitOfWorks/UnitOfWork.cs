using Microsoft.EntityFrameworkCore.Storage;
using Simuvirtu.Data;
using Simuvirtu.Interfaces;

namespace Simuvirtu.UnitOfWorks
{
    public class UnitOfWork : IUnitOfWork
    {
        private readonly ApplicationDbContext _db;

        public UnitOfWork(ApplicationDbContext db) => _db = db;

        public Task<int> SaveChangesAsync(CancellationToken ct = default) => _db.SaveChangesAsync(ct);

        public Task<IDbContextTransaction> BeginTransactionAsync(CancellationToken ct = default)
            => _db.Database.BeginTransactionAsync(ct);

        public Task CommitAsync(IDbContextTransaction tx, CancellationToken ct = default)
            => tx.CommitAsync(ct);

        public Task RollbackAsync(IDbContextTransaction tx)
            => tx.RollbackAsync();

        public ValueTask DisposeAsync() => _db.DisposeAsync();
    }
}
