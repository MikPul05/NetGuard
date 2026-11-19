  export function Pagination({ page, size, total, onChange }) {
    const pages = Math.max(1, Math.ceil(total / size))
    if (pages === 1) return null          // nothing to page through

    return (
      <div className="pager">
        <button disabled={page <= 1} onClick={() => onChange(page - 1)}>Previous</button>
        <span>Page {page} of {pages}</span>
        <button disabled={page >= pages} onClick={() => onChange(page + 1)}>Next</button>
      </div>
    )
  }