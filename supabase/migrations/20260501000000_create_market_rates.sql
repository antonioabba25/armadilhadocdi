-- Cache persistente de series oficiais usado pelo backend Supabase/Postgres.
-- A aplicacao tambem cria a tabela automaticamente, mas esta migracao deixa o
-- schema reproduzivel no SQL Editor ou via Supabase CLI.

create table if not exists public.market_rates (
  series text not null,
  ref_date date not null,
  value numeric not null,
  updated_at timestamptz not null default now(),
  primary key (series, ref_date)
);

alter table public.market_rates enable row level security;

comment on table public.market_rates is
  'Cache de series oficiais de mercado usadas pelo app Armadilha do CDI.';
comment on column public.market_rates.series is
  'Nome logico da serie, por exemplo cdi ou usd.';
comment on column public.market_rates.ref_date is
  'Data oficial de referencia do ponto da serie.';
comment on column public.market_rates.value is
  'Valor oficial normalizado como numeric.';

do $$
begin
  if exists (select 1 from pg_roles where rolname = 'anon') then
    revoke all on table public.market_rates from anon;
  end if;

  if exists (select 1 from pg_roles where rolname = 'authenticated') then
    revoke all on table public.market_rates from authenticated;
  end if;
end $$;
