// Lambda entry point: runs the sync against the site's S3 bucket. Invoked on a schedule.

import { S3Client, DeleteObjectCommand, ListObjectsV2Command, PutObjectCommand } from '@aws-sdk/client-s3';
import { sync } from './sync.mjs';

const s3 = new S3Client({});

function s3Store(bucket) {
  return {
    async list(prefix) {
      const keys = [];
      let ContinuationToken;
      do {
        const page = await s3.send(new ListObjectsV2Command({ Bucket: bucket, Prefix: prefix, ContinuationToken }));
        keys.push(...(page.Contents ?? []).map((object) => object.Key));
        ContinuationToken = page.NextContinuationToken;
      } while (ContinuationToken);
      return keys;
    },
    async put(key, body, { contentType, cacheControl }) {
      await s3.send(new PutObjectCommand({ Bucket: bucket, Key: key, Body: body, ContentType: contentType, CacheControl: cacheControl }));
    },
    async delete(key) {
      await s3.send(new DeleteObjectCommand({ Bucket: bucket, Key: key }));
    },
  };
}

export async function handler() {
  const result = await sync({
    store: s3Store(process.env.BUCKET),
    apiKey: process.env.ETSY_API_KEY,
    sharedSecret: process.env.ETSY_SHARED_SECRET,
    shopName: process.env.SHOP_NAME,
  });
  console.log(JSON.stringify(result));
  return result;
}
