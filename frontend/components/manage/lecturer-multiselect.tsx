'use client';

import { useId, useState } from 'react';

import { inputClass } from '@/components/manage/ui';

/** Multi-select of lecturers with a name filter; already-picked lecturers stay visible even
 * when they no longer match the search text, so filtering never silently drops a selection. */
export function LecturerMultiSelect({
  name,
  lecturers,
  defaultValue = [],
  size = 6,
  className = '',
}: {
  name: string;
  lecturers: { lecturer_id: string; name_th: string }[];
  defaultValue?: string[];
  size?: number;
  className?: string;
}) {
  const inputId = useId();
  const [query, setQuery] = useState('');
  const [selected, setSelected] = useState(new Set(defaultValue));

  const visible = lecturers.filter(
    (lecturer) => selected.has(lecturer.lecturer_id) || lecturer.name_th.includes(query)
  );

  return (
    <div>
      <label htmlFor={inputId} className="sr-only">
        ค้นหาชื่ออาจารย์
      </label>
      <input
        id={inputId}
        type="search"
        value={query}
        onChange={(event) => setQuery(event.target.value)}
        placeholder="ค้นหาชื่ออาจารย์"
        className={`${inputClass} mb-2`}
      />
      <select
        name={name}
        multiple
        size={size}
        defaultValue={defaultValue}
        onChange={(event) =>
          setSelected(new Set(Array.from(event.target.selectedOptions, (option) => option.value)))
        }
        className={`${inputClass} ${className}`}
      >
        {visible.map((lecturer) => (
          <option key={lecturer.lecturer_id} value={lecturer.lecturer_id}>
            {lecturer.name_th}
          </option>
        ))}
      </select>
    </div>
  );
}
