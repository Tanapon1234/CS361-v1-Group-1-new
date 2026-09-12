import { NextResponse } from 'next/server';

import masterData from '../../../../lib/v2/master-data.mjs';

export function masterDataResponse(getPayload) {
  try {
    return NextResponse.json(getPayload());
  } catch (error) {
    const { body, status } = masterData.formatMasterDataError(error);
    return NextResponse.json(body, { status });
  }
}
